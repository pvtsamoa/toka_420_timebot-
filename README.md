# Toka 420 Time Bot — Telegram Cannabis Ritual Bot

🌿⛵ **Weedcoin ritual bot** designed to call 420 in every time zone. This bot blesses one city at 4:20 PM in its respective time zone, checks current Weedcoin price action, and shares cannabis crypto news from around the world.

---

## Features
- Modular design (each service can be swapped or removed without breaking the bot)
- Telegram commands:
  - `/status` → check if the schedule is set and ready to deploy on time
  - `/news` → pull global cannabis and cannabis crypto news
  - `/studies` → cannabis research, health benefits, nutrition, land regeneration & whole plant awareness
  - `/token <symbol>` → fetch current Weedcoin price action and market trends
- Fail-open behavior (if a module fails, the bot keeps running)
- Simple JSON logging for state and prices
- The bot is anchored to Pacific Standard Time (PST) for all 4:20 calls.

---

## Setup
1. Clone this repo  
2. Install dependencies  
3. Copy `.env.example` to `.env` and add your TELEGRAM_BOT_TOKEN  
4. Run: `python app.py`

---

✨ *Keep your canoe balanced. Bongterm > FOMO.*
