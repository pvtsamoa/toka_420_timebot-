#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd ~/Toka_420_Timebot

# Load env and venv
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
[ -f .venv/bin/activate ] && . .venv/bin/activate

# Masked prints for quick sanity
TOK="${TELEGRAM_BOT_TOKEN:-missing}"
CID="${TELEGRAM_GLOBAL_CHAT_ID:-<none>}"
MASKED_TOKEN="$(printf '%s' "${TOK}" | sed -E 's/^(.{9}).*/\1********/')"  # 757771051********
echo "--- $(date -u) starting Toka ---"
echo "TELEGRAM_BOT_TOKEN: ${MASKED_TOKEN}"
echo "CHAT_ID: ${CID}"

# Start (tmux keeps it alive)
tmux has-session -t toka420 2>/dev/null && tmux kill-session -t toka420
tmux new-session -d -s toka420 "python app.py >> logs/bot.log 2>&1"
echo "Started Toka in tmux session 'toka420'."
echo "Logs: $(pwd)/logs/bot.log"
echo "View: tmux attach -t toka420"
