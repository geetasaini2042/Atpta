import os
import requests
from pyrogram import Client, filters
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from flask import Flask
from load_bot_data import download_entire_bot_data
flask_app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bots_sync.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
# ✅ .env फाइल लोड करें
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOTS_JSON_URL = "https://botdata123.singodiya.tech/bots.json"

# ✅ Pyrogram Client बनाएँ
bot = Client(
    "BotixHubBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)
@flask_app.route("/")
def home():
    return "Hi, I AM BOTIXHUBBOT"
    
def run_bot():
    print("🤖 BotixHubBot Working...")
    download_entire_bot_data()
    bot.run()
    logging.info("Stopped\n")

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)