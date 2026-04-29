#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

LOGFILE="logs/bot.log"
[ -f "$LOGFILE" ] || touch "$LOGFILE"
echo "Tailing $LOGFILE (Ctrl+C to exit)"
tail -f "$LOGFILE"
