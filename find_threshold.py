#!/usr/bin/env python3
# find_threshold.py
# Analyzes CAN timing gaps to find optimal threshold
import sys
import re
import statistics

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

def find_gap_clusters(gaps, num_clusters=2):
    """Find distinct gap clusters using simple binning"""
    sorted_gaps = sorted(gaps)
    
    # Try to find a clear separation point
    # Look for the biggest jump between consecutive gaps
    max_jump = 0
    split_idx = len(sorted_gaps) // 2
    
    for i in range(1, len(sorted_gaps)):
        jump = sorted_gaps[i] - sorted_gaps[i-1]
        if jump > max_jump:
            max_jump = jump
            split_idx = i
    
    # Only consider it a valid split if the jump is significant
    if max_jump > sorted_gaps[split_idx-1] * 2:  # Jump is > 2x the previous value
        cluster1 = sorted_gaps[:split_idx]
        cluster2 = sorted_gaps[split_idx:]
        return cluster1, cluster2
    
    return None, None

def analyze_gaps(gaps):
    """Analyze gap distribution to find potential threshold"""
    if not gaps:
        return None
    
    sorted_gaps = sorted(gaps)
    
    print("\n" + "="*70)
    print("GAP STATISTICS")
    print("="*70)
    print(f"Total gaps: {len(gaps)}")
    print(f"Min gap:    {min(gaps):.6f}s")
    print(f"Max gap:    {max(gaps):.6f}s")
    print(f"Mean:       {statistics.mean(gaps):.6f}s")
    print(f"Median:     {statistics.median(gaps):.6f}s")
    
    print("\n" + "="*70)
    print("GAP DISTRIBUTION (Percentiles)")
    print("="*70)
    print(f"5th:   {sorted_gaps[len(sorted_gaps)//20]:.6f}s")
    print(f"25th:  {sorted_gaps[len(sorted_gaps)//4]:.6f}s")
    print(f"50th:  {sorted_gaps[len(sorted_gaps)//2]:.6f}s")
    print(f"75th:  {sorted_gaps[3*len(sorted_gaps)//4]:.6f}s")
    print(f"95th:  {sorted_gaps[19*len(sorted_gaps)//20]:.6f}s")
    
    # Try to find two distinct clusters
    cluster1, cluster2 = find_gap_clusters(gaps)
    
    if cluster1 and cluster2:
        avg1 = statistics.mean(cluster1)
        avg2 = statistics.mean(cluster2)
        threshold = (max(cluster1) + min(cluster2)) / 2
        
        print("\n" + "="*70)
        print("DETECTED GAP CLUSTERS (Bimodal Distribution)")
        print("="*70)
        print(f"Cluster 1 (SHORT): {len(cluster1)} gaps")
        print(f"  Range: {min(cluster1):.6f}s to {max(cluster1):.6f}s")
        print(f"  Average: {avg1:.6f}s")
        print(f"\nCluster 2 (LONG): {len(cluster2)} gaps")
        print(f"  Range: {min(cluster2):.6f}s to {max(cluster2):.6f}s")
        print(f"  Average: {avg2:.6f}s")
        
        print("\n" + "="*70)
        print("SUGGESTED THRESHOLD")
        print("="*70)
        print(f"Separation point: {threshold:.6f}s")
        print(f"(Midpoint between {max(cluster1):.6f}s and {min(cluster2):.6f}s)")
        print(f"\n🎯 RECOMMENDED THRESHOLD: {threshold:.6f}s")
        print("="*70)
        
        return threshold
    else:
        # Fallback: use median as threshold
        print("\n" + "="*70)
        print("WARNING: No clear bimodal distribution detected")
        print("="*70)
        print("Falling back to median as threshold")
        
        # Find most common gaps
        hist = {}
        for g in gaps:
            bucket = round(g, 6)
            hist[bucket] = hist.get(bucket, 0) + 1
        
        top_gaps = sorted(hist.items(), key=lambda x: x[1], reverse=True)[:10]
        
        print("\n" + "="*70)
        print("MOST COMMON GAP VALUES")
        print("="*70)
        for i, (gap, count) in enumerate(top_gaps, 1):
            pct = 100 * count / len(gaps)
            print(f"{i:2}. {gap:.6f}s → {count:4} times ({pct:5.1f}%)")
        
        threshold = statistics.median(gaps)
        
        print("\n" + "="*70)
        print("SUGGESTED THRESHOLD")
        print("="*70)
        print(f"🎯 RECOMMENDED THRESHOLD: {threshold:.6f}s (median)")
        print("="*70)
        
        return threshold

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 find_threshold.py <logfile> <CAN_ID>")
        print("\nExample: python3 find_threshold.py dif3.log 6F2")
        sys.exit(1)
    
    logfile = sys.argv[1]
    canid = sys.argv[2].upper()
    
    print(f"\n[+] Analyzing {logfile} for CAN ID {canid}...")
    ts = parse_timestamps(logfile, canid)
    
    if not ts:
        print("[-] No timestamps found!")
        sys.exit(1)
    
    print(f"[+] Found {len(ts)} frames")
    
    gaps = gaps_from_timestamps(ts)
    print(f"[+] Calculated {len(gaps)} time gaps")
    
    threshold = analyze_gaps(gaps)
    
    if threshold:
        print(f"\nℹ️  Use this threshold in the decoder:")
        print(f"   python3 time_decode.py {logfile} {canid} {threshold:.6f}")
    else:
        print("\n[-] Could not determine threshold automatically")
        print("    Try manual inspection of the gap values above")