import os,json
from dotenv import load_dotenv
from pyrogram.filters import Filter
load_dotenv()
import requests
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ALT_REPO = "geetasaini2042/Database"
ALT_GITHUB_TOKEN = os.getenv("ALT_GITHUB_TOKEN")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

status_user_file = os.path.join(BASE_PATH, "status_user.json")

class StatusFilter(Filter):
    def __init__(self, status_prefix):
        self.status_prefix = status_prefix

    async def __call__(self, client, message):
        user_id = str(message.from_user.id)

        try:
            with open(status_user_file, "r") as f:
                status_data = json.load(f)
        except:
            return False

        current_status = status_data.get(user_id, "")
        return current_status.startswith(self.status_prefix)

import requests

BOT_DATA_URL = "https://botdata123.singodiya.tech/all_registered_bot.json"

def get_bot_username(bot_id: str) -> str:
    """
    🔹 Given a bot_id, fetch the username from remote JSON.
    Returns username as string or 'N/A' if not found.
    """
    try:
        response = requests.get(BOT_DATA_URL, timeout=10)
        if response.status_code != 200:
            return "N/A"
        bots_data = response.json()
        for user_info in bots_data.values():
            bots = user_info.get("bots", {})
            if bot_id in bots:
                return bots[bot_id].get("username", "N/A")
        return "N/A"
    except Exception as e:
        print(f"[ERROR] Failed to fetch bot username: {e}")
        return "N/A"
