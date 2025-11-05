#!/usr/bin/env bash
# scan_rtr_nocapture.sh
# Sends RTR frames for a range of 11-bit CAN IDs without capturing responses.
# Usage:
#   sudo ./scan_rtr_nocapture.sh [IF] [START_HEX] [END_HEX] [DLC] [DELAY]
# Example:
#   sudo ./scan_rtr_nocapture.sh can0 0x000 0x7FF 8 0.01

IF=${1:-can0}
START_HEX=${2:-0x000}
END_HEX=${3:-0x7FF}
DLC=${4:-8}
DELAY=${5:-0.01}   # seconds between sends (float)

# convert hex args to integers (bash handles 0xNN automatically)
START=$((START_HEX))
END=$((END_HEX))

if (( START < 0 || END < 0 || START > 0x7FF || END > 0x7FF || START > END )); then
  echo "Invalid range. Valid 11-bit range is 0x000..0x7FF and START <= END."
  exit 1
fi

echo "[*] Interface: $IF"
printf "[*] Scanning IDs from 0x%03X to 0x%03X (DLC=%s, delay=%s s)\n" "$START" "$END" "$DLC" "$DELAY"
echo "[*] Run 'candump -L $IF' in another terminal to capture replies."

# main loop: send RTR frames only (no capture)
for (( id=START; id<=END; id++ )); do
  idhex=$(printf "%03X" "$id")
  # send RTR with specified DLC. Uses cansend syntax: <id>#R<dlc>
  cansend "$IF" "${idhex}#R${DLC}" >/dev/null 2>&1 || {
    echo "[!] cansend failed for ID 0x$idhex (check interface/permissions)"
    exit 2
  }
  # small progress output every 128 IDs (adjust as you like)
  if (( (id - START) % 128 == 0 )); then
    printf "[*] Sent up to 0x%03X\n" "$id"
  fi
  # delay to avoid saturating bus
  sleep "$DELAY"
done

echo "[+] Done scanning range 0x$(printf '%03X' $START) .. 0x$(printf '%03X' $END)"
exit 0

