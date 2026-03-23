# Toka 420 Time Bot — Telegram Cannabis Ritual Bot

Weedcoin ritual bot that fires at local 4:20 AM/PM, blesses your day or night,
checks token action, highlights cannabis culture, and closes with a Weedcoin OG
joke/meme rotation.

---

## Features
- Modular design (each service can be swapped or removed without breaking the bot)
- Telegram commands:
  - `/blessnow` → manually push the current Green Hours blessing right now
  - `/news` → pull global cannabis and cannabis crypto news
  - `/token <symbol>` → fetch current Weedcoin price action and market trends
  - `/health` → quick health check
- Automated ritual includes:
  - Day/night blessing
  - Weedcoin price anchor
  - Scam/safety warning
  - Cannabis culture line
  - Weedcoin OG meme/joke closer
  - Optional real-time X mirror (same ritual text posted when Telegram sends)
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
- `JOKE_BLACKLIST_TERMS` (comma-separated blocked terms)

Optional env vars for real-time X mirroring:
- `X_POST_ENABLED` (`true`/`false`)
- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `X_POST_MAX_ATTEMPTS` (default `1` for time-sensitive single-attempt posting)

---

✨ *Keep your canoe balanced. Bongterm > FOMO.*
