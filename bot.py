import os
import telebot
import requests
import json
import re
import time
from dotenv import load_dotenv

# ---------- Load .env ----------
load_dotenv()

# ---------- CONFIG ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MAX_CHUNK = 3800

# ---------- Helpers ----------
def safe_send(chat_id, text):
    if not text:
        return
    if len(text) <= MAX_CHUNK:
        bot.send_message(chat_id, text)
        return
    cur = ""
    for line in text.splitlines(True):
        if len(cur) + len(line) > MAX_CHUNK:
            bot.send_message(chat_id, cur)
            time.sleep(0.12)
            cur = line
        else:
            cur += line
    if cur:
        bot.send_message(chat_id, cur)

def pretty_json(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except:
        return str(obj)

def is_potential_mobile(text):
    digits = re.sub(r'\D', '', text)
    return len(digits) >= 10

def last_10_digits(text):
    digits = re.sub(r'\D', '', text)
    return digits[-10:] if len(digits) >= 10 else digits

# ---------- Bot handlers ----------
@bot.message_handler(commands=['start', 'help'])
def cmd_start(m):
    txt = ("👋 <b>Welcome to TEAM ox1</b>\n\n"
           "🔍 Send a <b>10-digit mobile number</b> and I will query the API.\n\n"
           "🔴 <b>Developer :</b> @ox1_spark")
    bot.send_message(m.chat.id, txt)

@bot.message_handler(func=lambda msg: True)
def handle_all(msg):
    chat_id = msg.chat.id
    text = msg.text.strip()

    if not is_potential_mobile(text):
        bot.send_message(chat_id, "⚠️ Please send a valid 10-digit mobile number.")
        return

    mobile = last_10_digits(text)
    bot.send_message(chat_id, f"⏳ Querying API for: <code>{mobile}</code>")

    params = {"key": API_KEY, "mobile": mobile}
    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    except requests.exceptions.RequestException as e:
        bot.send_message(chat_id, f"❌ API request failed: {e}")
        return

    if resp.status_code != 200:
        bot.send_message(chat_id, f"🚫 API returned status {resp.status_code}")
        safe_send(chat_id, "<pre>" + resp.text[:2000] + "</pre>")
        return

    try:
        # Replace "by anish"
        text_data = resp.text.replace("by anish", "by @ox1_spark")
        try:
            data = json.loads(text_data)
            pretty = pretty_json(data)
        except:
            pretty = text_data
        safe_send(chat_id, "<pre>" + pretty[:3500] + "</pre>")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ Parsing error: {e}")

    bot.send_message(chat_id, "🔴 <b>Developer :</b> @ox1_spark")

# ---------- Run ----------
if name == "main":
    print("🤖 Bot is running...")
    bot.infinity_polling()
