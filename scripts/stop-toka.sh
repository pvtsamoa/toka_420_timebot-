#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
SESSION="toka420"
if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION"
  echo "Stopped tmux session '$SESSION'."
else
  pkill -f "python app.py" 2>/dev/null || true
  echo "No tmux session. Killed any stray python app.py."
fi
