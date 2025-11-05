#!/usr/bin/env bash
DEV=/dev/ttyACM1
LOG=serial_probe_$(date +%Y%m%d_%H%M%S).log

# small command list (edit/add more)
cmds=(
  "HELP"
  "?"
  "COMMAND"
  "GET FLAG"
  "GETFLAG"
  "GETFLAG()"
  "FLAG"
  "flags"
  "ID"
  "INFO"
  "STATUS"
  "VERSION"
  "VER"
  "READ"
  "DUMP"
  "WHO"
  "WHOAMI"
  "HELLO"
  "PING"
  "RESET"
  "REBOOT"
  "ADMIN"
)

echo "Logging to $LOG"
# start background monitor (non-blocking)
stdbuf -o0 cat "$DEV" | tr -cd '\11\12\15\40-\176' > "$LOG" &
MON_PID=$!
sleep 0.2

for c in "${cmds[@]}"; do
  echo ">>> Sending: $c"
  printf '%s\r\n' "$c" | sudo tee "$DEV" > /dev/null
  sleep 0.6
done

# give device a moment then kill monitor
sleep 1
kill $MON_PID 2>/dev/null || true

echo "Probe finished. Check $LOG"

