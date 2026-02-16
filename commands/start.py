"""
/start command — Welcome and command reference
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with full command reference."""
    user_id = update.effective_user.id if update.effective_user else "unknown"
    logger.info("Start command requested (user: %s)", user_id)

    message = """
🌿⛵️ **Toka 420 Time Bot** — Welcome, Navigator ✨

Your guide through cannabis culture and cryptocurrency.
Every day, somewhere in the world, it is 4:20 — and Toka marks the moment.

────────────────────────

**📋 COMMANDS**

🟢 **/status**
Bot health, scheduler status, price anchor, and next 4:20 ritual

📰 **/news**
Rotating market news (crypto → finance)

🩺 **/health**
Quick bot health check

────────────────────────

**⏰ AUTOMATED RITUALS**

• Fires daily at **04:20 local time** in every active timezone  
• One ritual per timezone  
• Regional crypto hubs rotate daily  
• Cities within each hub rotate daily  

Each ritual includes:
• Price anchor (Weedcoin and featured token)
• Navigator’s Blessing
• Cryptocurrency safety reminder

The wave never stops — the spotlight moves.

────────────────────────

**💡 TIPS**

→ Use `/token weedcoin` to track price movement  
→ Use `/status` to confirm the next local 4:20  
→ Rituals run **24/7**, rolling across the globe  

────────────────────────

🌺 May the Navigator’s blessing guide your timing and your trades.
"""

    if update.effective_message:
        await update.effective_message.reply_text(message, parse_mode="Markdown")
