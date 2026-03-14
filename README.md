# Toka 420 Time Bot — Telegram Cannabis Ritual Bot

Weedcoin ritual bot that fires at local 4:20 AM/PM, blesses your day or night,
checks token action, highlights cannabis culture, and closes with a Weedcoin OG
joke/meme rotation.

---

## Features
- Modular design (each service can be swapped or removed without breaking the bot)
- Telegram commands:
  - `/status` → check if the schedule is set and ready to deploy on time
  - `/news` → pull global cannabis and cannabis crypto news
  - `/studies` → cannabis research, health benefits, nutrition, land regeneration & whole plant awareness
  - `/token <symbol>` → fetch current Weedcoin price action and market trends
- Automated ritual includes:
  - Day/night blessing
  - Weedcoin price anchor
  - Scam/safety warning
  - Cannabis culture line
  - Weedcoin OG meme/joke closer
- Persistent 15-day joke rotation (SQLite) with local fallback seeding
- Fail-open behavior (if a module fails, the bot keeps running)
- Simple JSON logging for state and prices
- Scheduler checks every minute and fires only when a timezone is at local 04:20 or 16:20.

---

## Setup
1. Clone this repo  
2. Install dependencies  
3. Copy `.env.example` to `.env` and add your TELEGRAM_BOT_TOKEN  
4. Run: `python app.py`

Optional env vars for external joke sources:
- `WEEDCOINOG_SITE_JOKES_URL`
- `WEEDCOINOG_X_JOKES_URL`
- `WEEDCOINOG_X_ACCOUNT_URL` (default: `https://x.com/weedcoinOG`)
- `WEEDCOINOG_X_COMMUNITY_URL` (default: `https://x.com/i/communities/1907131002478285013`)
- `JOKE_REDDIT_FEEDS` (comma-separated JSON feed URLs, set `off` to disable)
- `JOKE_BLACKLIST_TERMS` (comma-separated blocked terms, default includes `marijuana`)

---

✨ *Keep your canoe balanced. Bongterm > FOMO.*
