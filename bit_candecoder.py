#!/usr/bin/env python3
"""
Comprehensive CAN Flag Decoder
Handles multiple encoding methods commonly used in CTF challenges
Automatically find 1-8 bits in a log file
Can also be used to find bits in a remote can frame automatically
Usage: python3 bit_candecoder.py <logfile.txt> <arbid>
Example: python3 bit_candecoder.py inter2.log 6F1 
"""
import sys

def decode_bits_to_string(bit_string, reverse_each_byte=False, stop_at_brace=True):
    """Convert bit string to ASCII, optionally reversing each byte"""
    result = ''
    for i in range(0, len(bit_string), 8):
        if i + 8 <= len(bit_string):
            byte = bit_string[i:i+8]
            if reverse_each_byte:
                byte = byte[::-1]
            try:
                char_val = int(byte, 2)
                if char_val == ord('}') and stop_at_brace:
                    result += chr(char_val)
                    break
                elif 32 <= char_val <= 126:  # Printable ASCII
                    result += chr(char_val)
                else:
                    if stop_at_brace:
                        break
                    result += '.'
            except:
                result += '?'
    return result

def search_for_flag(bit_string, method_name):
    """Search for flag pattern and decode if found"""
    # Look for "flag" pattern in binary (MSB format)
    target = ''.join([format(ord(c), '08b') for c in "flag"])
    
    if target in bit_string:
        pos = bit_string.index(target)
        adjusted_bits = bit_string[pos:]
        result = decode_bits_to_string(adjusted_bits, False, True)
        
        if result.startswith('flag') and '}' in result:
            return result, pos
    
    # Also try LSB format
    result_lsb = decode_bits_to_string(bit_string, True, False)
    if 'flag{' in result_lsb.lower():
        flag_pos = result_lsb.lower().index('flag{')
        end_pos = result_lsb.find('}', flag_pos)
        if end_pos != -1:
            return result_lsb[flag_pos:end_pos+1], flag_pos * 8
    
    return None, -1

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 bit_candecoder.py <logfile> <can_id>")
        print("Example: python3 bit_candecoder.py capture.log 6F0")
        sys.exit(1)
    
    filename = sys.argv[1]
    can_id = sys.argv[2].upper()
    
    print("="*70)
    print("Comprehensive CAN Flag Decoder")
    print("="*70)
    print(f"Log file: {filename}")
    print(f"CAN ID: {can_id}")
    print("="*70)
    
    # Collect all frames
    frames = []
    with open(filename, 'r') as f:
        for line in f:
            if f'{can_id}#' in line:
                parts = line.strip().split()
                timestamp = parts[0].strip('()')
                msg_parts = parts[2].split('#')
                data = msg_parts[1] if len(msg_parts) > 1 else ''
                frames.append((timestamp, data))
    
    if not frames:
        print(f"\n❌ No frames found for CAN ID {can_id}")
        sys.exit(1)
    
    print(f"\nTotal frames collected: {len(frames)}")
    
    # Analyze frame types
    remote_frames = sum(1 for _, d in frames if d == 'R')
    empty_frames = sum(1 for _, d in frames if d == '' or d.strip() == '')
    data_frames = len(frames) - remote_frames - empty_frames
    
    print(f"  Remote frames (R): {remote_frames}")
    print(f"  Empty frames: {empty_frames}")
    print(f"  Data frames: {data_frames}")
    
    # Show sample of data frames
    if data_frames > 0:
        print(f"\nSample data frames:")
        count = 0
        for ts, data in frames:
            if data and data != 'R' and data.strip() != '':
                print(f"  {ts}: {can_id}#{data}")
                count += 1
                if count >= 5:
                    break
    
    print("\n" + "="*70)
    print("Trying different encoding methods:")
    print("="*70)
    
    methods = []
    
    # METHOD 1: LSB of data bytes (like 6F0 easy challenge)
    if data_frames > 0:
        bits = []
        for ts, data in frames:
            if data and data != 'R' and data.strip() != '':
                # Pad to even length
                if len(data) % 2 == 1:
                    data = '0' + data
                # Extract LSB from each byte
                for i in range(0, len(data), 2):
                    if i + 2 <= len(data):
                        try:
                            byte_val = int(data[i:i+2], 16)
                            bits.append(str(byte_val & 1))
                        except:
                            pass
        
        if bits:
            bit_string = ''.join(bits)
            methods.append(("Method 1: LSB from data bytes", bit_string))
    
    # METHOD 2: R=1, Empty=0 (like 6F1 intermediate challenge)
    if remote_frames > 0 and empty_frames > 0:
        bits = []
        for ts, data in frames:
            # Skip actual data frames
            if data and data != 'R' and data.strip() != '':
                continue
            if data == 'R':
                bits.append('1')
            else:  # Empty
                bits.append('0')
        
        if bits:
            bit_string = ''.join(bits)
            methods.append(("Method 2: R=1, Empty=0", bit_string))
    
    # METHOD 3: R=0, Empty=1 (opposite mapping)
    if remote_frames > 0 and empty_frames > 0:
        bits = []
        for ts, data in frames:
            # Skip actual data frames
            if data and data != 'R' and data.strip() != '':
                continue
            if data == 'R':
                bits.append('0')
            else:  # Empty
                bits.append('1')
        
        if bits:
            bit_string = ''.join(bits)
            methods.append(("Method 3: R=0, Empty=1", bit_string))
    
    # METHOD 4: All frames (including empty as 0x00)
    if empty_frames > 0:
        bits = []
        for ts, data in frames:
            if data == 'R':
                continue  # Skip remote frames
            elif data == '' or data.strip() == '':
                # Treat empty as 0x00 (bit=0)
                bits.append('0')
            else:
                # Extract LSB from data
                if len(data) % 2 == 1:
                    data = '0' + data
                for i in range(0, len(data), 2):
                    if i + 2 <= len(data):
                        try:
                            byte_val = int(data[i:i+2], 16)
                            bits.append(str(byte_val & 1))
                        except:
                            pass
        
        if bits:
            bit_string = ''.join(bits)
            methods.append(("Method 4: Empty=0x00, extract LSB from all", bit_string))
    
    # Try each method
    found_flags = []
    
    for method_name, bit_string in methods:
        print(f"\n{method_name}")
        print(f"  Bits collected: {len(bit_string)}")
        print(f"  First 80 bits: {bit_string[:80]}")
        
        # Try original bitstring
        flag, pos = search_for_flag(bit_string, method_name)
        if flag and flag.startswith('flag'):
            print(f"  ✓ Found at bit position {pos}")
            print(f"  🚩 FLAG: {flag}")
            found_flags.append((method_name, flag))
            continue
        
        # Try reversed bitstring
        reversed_bits = bit_string[::-1]
        flag, pos = search_for_flag(reversed_bits, method_name + " (reversed)")
        if flag and flag.startswith('flag'):
            print(f"  ✓ Found in REVERSED bitstring at position {pos}")
            print(f"  🚩 FLAG: {flag}")
            found_flags.append((method_name + " (reversed)", flag))
            continue
        
        # Show preview decode
        preview = decode_bits_to_string(bit_string[:min(400, len(bit_string))], False, False)
        print(f"  Preview: {preview[:60]}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY:")
    print("="*70)
    
    if found_flags:
        print(f"\n✓ Found {len(found_flags)} flag(s):")
        for method, flag in found_flags:
            print(f"  {method}")
            print(f"    🚩 {flag}")
    else:
        print("\n❌ No flags found. Try:")
        print("  1. Capture more data (longer duration)")
        print("  2. Check if trigger message is correct")
        print("  3. Verify CAN ID is correct")
        print("  4. Look for patterns in the preview decodes above")

if __name__ == "__main__":
    main()
