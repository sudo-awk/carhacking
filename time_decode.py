#!/usr/bin/env python3
# decode_flag.py
# Decodes CAN timing-based covert channel with given threshold
import sys
import re

def parse_timestamps(filename, canid):
    """Extract timestamps for a specific CAN ID"""
    ts = []
    pat = re.compile(r'\(?\s*([0-9]+\.[0-9]+)\s*\)?.*?\b' + re.escape(canid) + r'\b#')
    with open(filename, 'r', errors='ignore') as f:
        for line in f:
            m = pat.search(line)
            if m:
                try:
                    ts.append(float(m.group(1)))
                except:
                    pass
    return ts

def gaps_from_timestamps(ts):
    """Calculate time gaps between consecutive frames"""
    return [ts[i] - ts[i-1] for i in range(1, len(ts))]

def bits_from_gaps(gaps, threshold, short_is='1'):
    """Convert gaps to bits using threshold"""
    bits = []
    for g in gaps:
        bits.append(short_is if g < threshold else ('1' if short_is == '0' else '0'))
    return ''.join(bits)

def pack_bits_to_bytes(bitstr, offset=0, lsb_first=False):
    """Pack bit string into bytes"""
    out = []
    s = bitstr[offset:]
    for i in range(0, len(s), 8):
        chunk = s[i:i+8]
        if len(chunk) < 8:
            break
        out.append(int(chunk[::-1], 2) if lsb_first else int(chunk, 2))
    return out

def extract_flag(bs, max_search=200):
    """Extract complete flag - handles wrapped and reversed flags"""
    s = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bs)
    
    # Try forward
    flag_pos = s.lower().find('flag{')
    closing_pos = s.find('}')
    
    if flag_pos != -1 and closing_pos != -1:
        # Wrapped flag: flag{ at end, } at beginning
        if flag_pos > closing_pos:
            beginning = ''
            for i in range(min(closing_pos + 1, len(s))):
                char = s[i]
                if char != '.':
                    beginning += char
                if char == '}':
                    break
            
            ending = ''
            for i in range(flag_pos, len(s)):
                char = s[i]
                if char != '.':
                    ending += char
            
            result = ending + beginning
            if result.startswith('flag{') and '}' in result:
                return result
        
        # Normal sequential flag
        else:
            result = ''
            for i in range(flag_pos, min(flag_pos + max_search, len(s))):
                char = s[i]
                if char == '}':
                    result += char
                    break
                elif char != '.':
                    result += char
            if result.startswith('flag') and '}' in result:
                return result
    
    # Try byte-reversed
    bs_reversed = bs[::-1]
    s_reversed = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bs_reversed)
    
    flag_pos = s_reversed.lower().find('flag{')
    if flag_pos != -1:
        result = ''
        for i in range(flag_pos, min(flag_pos + max_search, len(s_reversed))):
            char = s_reversed[i]
            if char == '}':
                result += char
                break
            elif char != '.':
                result += char
        if result.startswith('flag') and '}' in result:
            return result
    
    return None

def try_all_combinations(gaps, threshold):
    """Try all parameter combinations to find the flag"""
    results = []
    
    for short_is in ['0', '1']:
        for offset in range(8):
            for lsb_first in [False, True]:
                bitstr = bits_from_gaps(gaps, threshold, short_is)
                bs = pack_bits_to_bytes(bitstr, offset, lsb_first)
                
                flag = extract_flag(bs)
                if flag and flag not in [r[4] for r in results]:
                    byte_order = "LSB" if lsb_first else "MSB"
                    results.append((short_is, offset, byte_order, lsb_first, flag))
    
    return results

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 decode_flag.py <logfile> <ARB_ID> <threshold>")
        print("\nExample: python3 decode_flag.py dif3.log 6F2 0.000791")
        print("\nTip: Use find_threshold.py first to determine the threshold")
        sys.exit(1)
    
    logfile = sys.argv[1]
    canid = sys.argv[2].upper()
    threshold = float(sys.argv[3])
    
    print(f"[+] Parsing {logfile} for CAN ID {canid}...")
    ts = parse_timestamps(logfile, canid)
    
    if not ts:
        print("[-] No timestamps found!")
        sys.exit(1)
    
    print(f"[+] Found {len(ts)} frames")
    
    gaps = gaps_from_timestamps(ts)
    print(f"[+] Calculated {len(gaps)} gaps")
    print(f"[+] Using threshold: {threshold:.6f}s")
    print(f"[+] Trying all parameter combinations...\n")
    
    results = try_all_combinations(gaps, threshold)
    
    if results:
        print("="*70)
        print(f"🎉 FOUND {len(results)} FLAG(S)!")
        print("="*70)
        
        for i, (short_is, offset, byte_order, lsb_first, flag) in enumerate(results, 1):
            print(f"\n[{i}] Flag: {flag}")
            print(f"    Parameters: short_is={short_is}, offset={offset}, byte_order={byte_order}")
        
        print("\n" + "="*70)
    else:
        print("="*70)
        print("❌ NO FLAG FOUND")
        print("="*70)
        print("\nTroubleshooting:")
        print("1. Try a different threshold (use find_threshold.py)")
        print("2. Verify the CAN ID is correct")
        print("3. Check if the log format is correct")
        
        # Show a sample decode for debugging
        print("\n[*] Sample decode (MSB, short=1, offset=0):")
        bitstr = bits_from_gaps(gaps, threshold, '1')
        bs = pack_bits_to_bytes(bitstr, 0, False)
        preview = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bs[:100])
        preview_rev = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bs[::-1][:100])
        print(f"    Forward:  {preview}")
        print(f"    Reversed: {preview_rev}")
