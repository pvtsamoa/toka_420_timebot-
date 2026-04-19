# Quick Start â€” Toka 420 Time Bot

ðŸš€ **Production Ready** | ðŸŸ¢ **All Critical Issues Fixed** | âœ… **Tested & Documented**

---

## 30-Second Deployment

```bash
# Option 1: Docker (Recommended)
docker build -t toka .
docker run --env-file .env toka

# Option 2: Systemd (Linux)
sudo cp toka.service /etc/systemd/system/
sudo systemctl enable toka && sudo systemctl start toka

# Check status
docker logs toka -f  # or: journalctl -u toka -f
```

---

## Configuration (.env)

```bash
TELEGRAM_BOT_TOKEN=123456:ABCdefGHIjklmnoPQRstuvWxyz
TELEGRAM_GLOBAL_CHAT_ID=-100123456789
TELEGRAM_SCOPE=all
DEFAULT_TOKEN=weedcoin
TZ=America/Los_Angeles
```

---

## Telegram Commands

| Command | Purpose |
|---------|---------|
| `/blessnow` | Trigger the current Green Hour blessing now |
| `/news` | Latest cannabis/crypto news |
| `/token [symbol]` | Token price lookup (default: $WEEDCOIN) |
| `/health` | Quick health check |

---

## Monitoring

```bash
# Docker
docker logs toka -f
docker stats toka

# Systemd
journalctl -u toka -f
systemctl status toka

# Check rituals
grep "ritual" logs/bot.log | tail -5
```

---

## Logs Location

- **Docker:** stdout (use `docker logs`)
- **Systemd:** journalctl (`journalctl -u toka -f`)
- **File:** `logs/bot.log`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "TELEGRAM_BOT_TOKEN missing" | Set in .env file |
| "TELEGRAM_GLOBAL_CHAT_ID not set" | Get from @userinfobot, add to .env |
| No rituals sent | Check logs for errors |
| High memory usage | Check log file size |
| API errors (429) | Wait 5-10 minutes |

---

## Key Files

- ðŸ“‹ [DEPLOYMENT.md](DEPLOYMENT.md) â€” Full deployment guide
- ðŸ” [PRODUCTION_REVIEW.md](PRODUCTION_REVIEW.md) â€” Comprehensive review
- âœ… [WORK_COMPLETED.md](WORK_COMPLETED.md) â€” What was fixed
- ðŸ³ [Dockerfile](Dockerfile) â€” Docker build
- âš™ï¸ [toka.service](toka.service) â€” Systemd service
- ðŸ§ª [tests/](tests/) â€” Unit tests

---

## Backup Data

```bash
# Backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# Restore
tar -xzf backup-20260115.tar.gz
systemctl restart toka
```

---

## Support

### Check Startup
```bash
python app.py
# Should show: âœ… Bot initialized successfully
```

### Validate Config
```bash
python -c "from services.config_validator import validate_config; validate_config()"
```

### Test Imports
```bash
python -c "import telegram; from services.ritual_time import ritual_call; print('âœ… OK')"
```

---

## Resources

- ðŸ¤– [Telegram Bot API](https://core.telegram.org/bots/api)
- ðŸ“Š [DexScreener API](https://docs.dexscreener.com/)
- ðŸ³ [Docker Docs](https://docs.docker.com/)
- ðŸ”§ [Systemd Docs](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**Version:** 1.0 (Production Ready)  
**Last Updated:** January 15, 2026  
**Status:** ðŸŸ¢ READY TO DEPLOY
