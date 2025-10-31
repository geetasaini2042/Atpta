import os
import json
import requests
import logging
from common_data import BASE_PATH, ALT_GITHUB_TOKEN, ALT_REPO

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

GITHUB_TOKEN = ALT_GITHUB_TOKEN
GITHUB_REPO = ALT_REPO
if not GITHUB_TOKEN:
    logging.error("❌ GitHub Token नहीं मिला! कृपया GITHUB_TOKEN env में सेट करें।")
    exit(1)

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ---------- Recursive Downloader ----------
def download_folder_from_github(api_url, local_folder):
    """GitHub से किसी भी फोल्डर (recursive) को डाउनलोड करे"""
    try:
        response = requests.get(api_url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(response.json())
            logging.error(f"❌ {api_url} एक्सेस नहीं हो सका ({response.status_code})")
            return

        items = response.json()
        if isinstance(items, dict) and items.get("message"):
            logging.error(f"GitHub Error: {items.get('message')}")
            return

        for item in items:
            name = item["name"]
            local_path = os.path.join(local_folder, name)

            if item["type"] == "dir":
                os.makedirs(local_path, exist_ok=True)
                download_folder_from_github(item["url"], local_path)

            elif item["type"] == "file":
                try:
                    file_data = requests.get(item["download_url"], headers=HEADERS, timeout=20)
                    if file_data.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(file_data.content)
                        logging.info(f"✅ Downloaded: {local_path}")
                    else:
                        logging.warning(f"⚠️ File download failed: {name} ({file_data.status_code})")
                except Exception as e:
                    logging.error(f"❌ File download error for {name}: {e}")

    except Exception as e:
        logging.error(f"❌ Recursive error at {api_url}: {e}")

# ---------- Master Function ----------
def download_entire_bot_data():
    """GitHub से पूरा BOT_DATA फोल्डर डाउनलोड करे"""
    base_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/BOT_DATA"
    local_base_dir = os.path.join(BASE_PATH, "BOT_DATA")
    os.makedirs(local_base_dir, exist_ok=True)

    logging.info("🚀 GitHub से पूरा BOT_DATA डाउनलोड शुरू हो रहा है...")
    download_folder_from_github(base_api_url, local_base_dir)
    logging.info("✅ पूरा BOT_DATA डाउनलोड पूरा हो गया।")
