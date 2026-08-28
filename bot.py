"""
Telegram Customer Support Bot
-------------------------------
A natural-sounding support chatbot for your business. No database, no
subscriptions - just conversation. It uses Groq's free LLM API to generate
replies in a professional-but-warm tone, grounded in the business info
you fill in below.

Setup:
  pip install -r requirements.txt
  env vars needed:
    BOT_TOKEN=...      (from @BotFather)
    GROQ_API_KEY=...   (free, from console.groq.com)

Run:
  python bot.py
"""

import logging
import os

from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")

# Initialize Groq client with explicit API key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY not set in environment variables")

# Create client with explicit API key
client = Groq(
    api_key=GROQ_API_KEY,
)

MODEL = "llama-3.3-70b-versatile"  # free on Groq; check console.groq.com for current model names

# ---------------------------------------------------------------------
# EDIT THIS: everything the bot knows about your business.
# Be as specific as you want for services you're happy to detail in chat.
# For anything you'd rather not detail here, just tell it to point people
# to your channel instead.
# ---------------------------------------------------------------------
SYSTEM_PROMPT = """You are a customer support assistant for [throne network],
speaking directly with customers on Telegram. Tone: professional but warm -
like a helpful real person, not a corporate script. Keep replies short and
conversational (2-4 sentences unless more detail is genuinely needed).

Services you can discuss in full detail:

1. Instagram Monitor Bot - $15/month
   Watches any public Instagram account and alerts the customer the moment
   the profile picture or username changes. Checks run every 30 seconds.

2. YouTube Monitor Bot - $20/month
   Same idea for a YouTube channel - alerts on name or profile picture
   changes. Checks run every 30 seconds.

For any other service someone asks about, do NOT give pricing or details
yourself. Instead, warmly tell them to check the latest post in our channel
for full info: https://t.me/thronenet - and that you're happy to answer
follow-up questions once they've had a look.

General behavior:
- If someone just says "hi"/"hello", greet them and ask how you can help.
- Answer naturally based on what they actually ask - don't dump the whole
  service list unprompted.
- If you don't know something, say so honestly and offer to check/follow up,
  don't make things up.
- Never claim to be human if directly asked - you can say you're the
  business's assistant.
"""

# In-memory conversation history per chat (resets if the bot restarts)
conversations: dict[int, list] = {}
MAX_HISTORY_MESSAGES = 20  # trim so old chats don't grow forever


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conversations[update.effective_chat.id] = []
    await update.message.reply_text(
        "Hi! How can I help you today?"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    history = conversations.setdefault(chat_id, [])
    history.append({"role": "user", "content": text})
    history[:] = history[-MAX_HISTORY_MESSAGES:]  # keep it bounded

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        reply_text = (
            "Sorry, I'm having trouble responding right now - "
            "please try again in a moment."
        )

    history.append({"role": "assistant", "content": reply_text})
    await update.message.reply_text(reply_text)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot starting (polling mode)...")
    app.run_polling()


if __name__ == "__main__":
    main() main()