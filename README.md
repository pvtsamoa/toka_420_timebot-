# Toka 420 Pulse

Lean Telegram bot focused on one clear loop:

1. It is always 4:20 somewhere.
2. You get a blessing when a timezone hits 4:20.
3. You get a live market pulse with Weedcoin first.
4. You get relevant cannabis + crypto headlines.

## What It Does

- Tracks global timezones and detects local 4:20 windows.
- Sends one ritual message with blessing and market context.
- Shows market momentum:
  - Weedcoin OG first
  - 24h top gainer
  - 24h top loser
  - Trending coin
  - Breadth snapshot
- Aggregates cannabis and crypto RSS headlines.

## Commands

- `/start` overview of purpose
- `/status` bot pulse + market snapshot + next check
- `/news` cannabis + crypto headlines
- `/health` liveness check

These are the only bot commands in the trimmed build.

## Setup

### Requirements

- Python 3.10+
- Telegram bot token
- Telegram chat ID for ritual messages

### Install

```bash
pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and fill values:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_GLOBAL_CHAT_ID=your_chat_id_here
DEFAULT_TOKEN=weedcoin
TZ=America/Los_Angeles
```

### Run

```bash
python app.py
```

## Project Layout

- `app.py` bot bootstrap and command wiring
- `scheduler.py` timezone scan and 4:20 triggers
- `commands/` Telegram command handlers
- `services/` market, ritual, persistence, and safety logic
- `media/` hubs, quotes, safety, token metadata
- `data/` persisted runtime settings
- `logs/` runtime logs

## Config Notes

Required:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_GLOBAL_CHAT_ID`

Optional:
- `DEFAULT_TOKEN` default market anchor token id
- `TZ` scheduler timezone baseline

## Troubleshooting

- Bot does not start:
  - verify `.env` values
  - verify dependency install from `requirements.txt`
- No ritual messages:
  - verify `TELEGRAM_GLOBAL_CHAT_ID`
  - ensure bot has permission in target group/channel
- Market lines show n/a:
  - upstream APIs may be rate-limited or unavailable

## Scope Philosophy

This repo intentionally avoids feature sprawl.

Everything should support the core pulse:
- 4:20 detection
- blessing
- market context
- cannabis + crypto headlines
