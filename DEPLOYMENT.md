# Toka 420 Time Bot â€” Deployment Guide

**Last Updated:** January 15, 2026  
**Status:** Production Ready (with monitoring)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Systemd Deployment (Linux)](#systemd-deployment-linux)
5. [Configuration](#configuration)
6. [Monitoring & Logs](#monitoring--logs)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Python 3.11+ (for bare metal) or Docker
- 2GB RAM minimum
- 100MB disk space (logs/data can grow)
- Internet access (for Telegram API, DexScreener, RSS feeds)
- Linux/macOS recommended (Windows WSL2 supported)

### Required Credentials
1. **TELEGRAM_BOT_TOKEN** â€” Get from [BotFather](https://t.me/BotFather)
2. **TELEGRAM_GLOBAL_CHAT_ID** â€” Chat ID where rituals will be posted
   ```bash
   # Get your chat ID: https://t.me/userinfobot
   ```

---

## Environment Setup

### 1. Create Environment File

```bash
cd /opt/toka  # or your chosen directory
cp .env.example .env
```

### 2. Configure .env

```bash
# Required
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_GLOBAL_CHAT_ID=YOUR_CHAT_ID_HERE

# Optional (defaults provided)
TELEGRAM_SCOPE=all              # all|apac|emea|amer
DEFAULT_TOKEN=weedcoin          # Default crypto token
WEEDCOIN_TOKEN=Weedcoin         # Weedcoin symbol
TZ=America/Los_Angeles          # Timezone for reference
```

### 3. Validate Configuration

```bash
python3 app.py
# Should output:
# âœ… Environment loaded from .env
# âœ… All required configuration validated
# âœ… Bot initialized successfully
# ðŸš€ Starting polling...
```

---

## Docker Deployment

### Build Image

```bash
docker build -t toka:latest .
```

### Run Container

```bash
docker run \
  --name toka \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  toka:latest
```

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  toka:
    build: .
    container_name: toka-bot
    env_file: .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Start:
```bash
docker-compose up -d
docker-compose logs -f
```

---

## Systemd Deployment (Linux)

### 1. Create User

```bash
sudo useradd -r -s /bin/bash toka
```

### 2. Set Up Directory

```bash
sudo mkdir -p /opt/toka
sudo chown -R toka:toka /opt/toka
sudo -u toka git clone <repo> /opt/toka
cd /opt/toka
```

### 3. Install Dependencies

```bash
sudo -u toka python3 -m venv .venv
sudo -u toka .venv/bin/pip install -r requirements.txt
```

### 4. Copy Service File

```bash
sudo cp toka.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 5. Configure Environment

```bash
sudo cp .env.example /opt/toka/.env
sudo nano /opt/toka/.env  # Edit with your tokens
sudo chown toka:toka /opt/toka/.env
sudo chmod 600 /opt/toka/.env
```

### 6. Start Service

```bash
sudo systemctl enable toka
sudo systemctl start toka
sudo systemctl status toka

# View logs
sudo journalctl -u toka -f
```

---

## Configuration

### Hubs Configuration

Edit `data/hubs.json` to customize which cities get 4:20 rituals:

```json
[
  {"name": "Tokyo", "tz": "Asia/Tokyo"},
  {"name": "Singapore", "tz": "Asia/Singapore"},
  {"name": "Sydney", "tz": "Australia/Sydney"},
  {"name": "Dubai", "tz": "Asia/Dubai"},
  {"name": "London", "tz": "Europe/London"},
  {"name": "New York", "tz": "America/New_York"},
  {"name": "Chicago", "tz": "America/Chicago"},
  {"name": "Los Angeles", "tz": "America/Los_Angeles"},
  {"name": "Honolulu", "tz": "Pacific/Honolulu"}
]
```

### Media Files

Customize ritual content:
- `media/jokes.json` â€” Humor
- `media/safety.json` â€” Safety tips
- `media/proverbs.json` â€” Wisdom
- `media/market.json` â€” Market tips

---

## Monitoring & Logs

### Log Location

**Docker:** Logs stream to stdout (use `docker logs toka`)  
**Systemd:** Logs to journalctl (`journalctl -u toka -f`)  
**File:** `logs/bot.log`

### Log Format

```
2026-01-15 16:20:00 | INFO     | app                  | ðŸŒ¿â›µ Toka 420 Time Bot v1 Starting
2026-01-15 16:20:01 | INFO     | services.ritual_time | ðŸŒŠ Starting ritual for Tokyo with token=weedcoin
2026-01-15 16:20:02 | INFO     | services.ritual_time | âœ… Ritual sent successfully for Tokyo
```

### Health Check

Check bot status:
```bash
# Via Telegram
/health

# Logs indicate
grep "ritual_call" logs/bot.log | tail -5
```

### Monitor Uptime

```bash
# Systemd
systemctl is-active toka

# Docker
docker ps --filter name=toka
```

---

## Backup & Recovery

### Automated Backup (Daily at 2 AM)

Create `/opt/toka/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/toka"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/data-$(date +%Y%m%d).tar.gz" /opt/toka/data/
tar -czf "$BACKUP_DIR/logs-$(date +%Y%m%d).tar.gz" /opt/toka/logs/
# Keep last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

Add to crontab:
```bash
sudo crontab -e
# 0 2 * * * /opt/toka/backup.sh
```

### Restore

```bash
tar -xzf backups/data-20260115.tar.gz -C /
systemctl restart toka
```

---

## Troubleshooting

### Bot Won't Start

```bash
# Check logs
systemctl status toka -n 50
journalctl -u toka -n 100

# Validate config
python3 -c "from services.config_validator import validate_config; validate_config()"

# Test imports
python3 -c "import telegram; print(telegram.__version__)"
```

### Missing TELEGRAM_GLOBAL_CHAT_ID

```bash
# Error in logs: "TELEGRAM_GLOBAL_CHAT_ID not set"

# Solution:
1. Get chat ID from @userinfobot
2. Update .env: TELEGRAM_GLOBAL_CHAT_ID=123456789
3. Restart: systemctl restart toka
```

### API Rate Limits

```bash
# Error: "429 Too Many Requests"

# Solutions:
- Add cooldown to commands
- Reduce feed refresh frequency
- Use DexScreener cache (60s TTL)
```

### Disk Space Issues

```bash
# Check log size
du -h logs/

# Rotate logs
find logs/ -name "*.log" -mtime +30 -delete

# Or use logrotate (Linux):
sudo cat > /etc/logrotate.d/toka << EOF
/opt/toka/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
}
EOF
```

### Telegram Connection Lost

```bash
# Bot automatically reconnects with exponential backoff
# Check status:
systemctl status toka

# Manual restart:
systemctl restart toka
```

---

## Performance Tips

1. **Reduce Feed Requests:** Cache results for 60+ seconds
2. **Batch Commands:** Group related operations
3. **Monitor Memory:** `systemctl status toka | grep Memory`
4. **Limit Log Files:** Use log rotation

---

## Security Hardening

1. **Restrict File Permissions**
   ```bash
   chmod 600 .env
   chmod 600 toka.service
   ```

2. **Use Systemd Security**
   ```bash
   systemctl --no-pager show toka | grep Security
   ```

3. **Firewall (Optional)**
   ```bash
   # No inbound ports needed for Telegram polling
   sudo ufw default deny incoming
   sudo ufw allow out to any port 443  # HTTPS only
   ```

4. **Secrets Management**
   - Never commit `.env` to git
   - Use `.env.example` for documentation
   - Rotate tokens regularly

---

## Maintenance Schedule

| Frequency | Task |
|-----------|------|
| Daily | Check logs for errors |
| Weekly | Review bot status |
| Monthly | Rotate logs, backup data |
| Quarterly | Update dependencies |
| Annually | Security audit |

---

## Support & Escalation

### Common Issues

| Issue | Solution |
|-------|----------|
| No rituals sent | Check TELEGRAM_GLOBAL_CHAT_ID |
| Slow commands | Clear cache, restart bot |
| High memory | Check log file size |
| API errors | Wait 5-10 min (rate limit) |

### Get Help

```bash
# Check logs
journalctl -u toka --since "10 minutes ago"

# Test connectivity
curl -I https://api.telegram.org
curl -I https://api.dexscreener.com

# Validate config
python3 services/config_validator.py
```

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Identify issue
systemctl status toka

# 2. Restore from backup
tar -xzf backups/data-20260114.tar.gz -C /

# 3. Restart
systemctl restart toka

# 4. Verify
systemctl status toka
```

---

**Last Reviewed:** 2026-01-15  
**Next Review:** 2026-02-15
