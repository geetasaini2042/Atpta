import os
import requests
from pyrogram import Client, filters
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from script import bot
from onlyfunctions import get_webhook_base_url, get_bot_token_by_id, is_premium_active
#from dotenv import load_dotenv
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bots_sync.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_LIST_URL = "https://botdata123.singodiya.tech/all_registered_bot.json"

def load_remote_bots_data():
    """🔹 Load all registered bots data from remote JSON"""
    try:
        response = requests.get(BOT_LIST_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Failed to load bot data: HTTP {response.status_code}")
            return {}
    except Exception as e:
        print(f"[EXCEPTION] Error loading bots data: {e}")
        return {}


@bot.on_callback_query(filters.regex(r"^bots_list_page_(\d+)$"))
async def bots_list_page_cb(client, query):
    user_id = str(query.from_user.id)
    page = int(query.data.split("_")[-1])

    # 🔹 Fetch bots data
    bots_data = load_remote_bots_data()
    user_info = bots_data.get(user_id, {})
    user_bots = user_info.get("bots", {})
    buttons = [
        [
            InlineKeyboardButton("➕️ Create New Bot", callback_data="add_new_bot")
        ]
    ]
    if not user_bots:
        await query.message.edit_text("😕 No bots found for your account.",reply_markup=InlineKeyboardMarkup(buttons))
        return

    # 🔹 Pagination setup
    bots_list = list(user_bots.items())
    bots_per_page = 10
    total_pages = (len(bots_list) - 1) // bots_per_page + 1
    start = (page - 1) * bots_per_page
    end = start + bots_per_page
    bots_page = bots_list[start:end]

    text = f"🤖 **Please select a Bot to manage:**\n\n"
    buttons = []

    # 🔹 Generate bot buttons
    for bot_id, bot_info in bots_page:
        username = bot_info.get("username", "N/A")
        buttons.append([
            InlineKeyboardButton(
                f"@{username}",
                callback_data=f"bot_details_{bot_id}"
            )
        ])

    # 🔹 Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"bots_list_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"bots_list_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    # 🔹 Back to home button
    buttons.append([InlineKeyboardButton("🏠 Back to Home", callback_data="back_to_home")])

    # 🔹 Send updated message
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )
import requests
import base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

user_pages = {}  # track user current page if needed

def load_remote_bots_data():
    """Load all registered bots from the main JSON"""
    try:
        resp = requests.get(BOT_LIST_URL, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch bots data: {e}")
    return {}


def fetch_bot_details(webhook_base_url):
    """Fetch individual bot details JSON from remote URL"""
    try:
        encoded_url = base64.b64encode(webhook_base_url.encode()).decode()
        url = f"https://botdata123.singodiya.tech/{encoded_url}/bots.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[ERROR] Failed to fetch bot details: {e}")
    return {}


@bot.on_callback_query(filters.regex(r"^bot_details_(\d+)$"))
async def bot_details_cb(client, query):
    bot_id = query.data.split("_")[-1]

    # Load main bot list to get webhook_base_url
    bots_data = load_remote_bots_data()

    user_bot_info = None
    webhook_base_url = None
    for user_info in bots_data.values():
        for b_id, b in user_info.get("bots", {}).items():
            if b_id == bot_id:
                webhook_base_url = b.get("webhook_base_url")
                break
        if webhook_base_url:
            break

    if not webhook_base_url:
        await query.answer("⚠️ Bot not found! Please Wait for server update and try again after 30 seconds.", show_alert=True)
        return

    # Fetch individual bot details
    bot_details = fetch_bot_details(webhook_base_url)
    bot_info = bot_details.get(bot_id)
    is_premium = is_premium_active(bot_id)
    if not bot_info:
        await query.answer("⚠️ Bot details not available!", show_alert=True)
        return

    # Compose message
    text = (
        f"🔹 **Username:** @{bot_info.get('username', 'N/A')}\n"
        f"🆔 **Bot ID:** `{bot_id}`\n"
        f"💎 Premium: {'✅' if is_premium else '❌'}\n"
        f"💰 Monetized: {'✅' if bot_info.get('is_monetized') else '❌'}\n"
        f"👤 Owner ID: `{bot_info.get('owner_id', 'N/A')}`"
    )

    user_id = query.from_user.id
    current_page = user_pages.get(user_id, 1)

    # Action buttons
    buttons = [
        [InlineKeyboardButton("🔄 Revoke Token", callback_data=f"revoke_{bot_id}"),
         InlineKeyboardButton("👮 Manage Admins", callback_data=f"manage_admins_{bot_id}")],
        [InlineKeyboardButton("🔁 Transfer Ownership", callback_data=f"transfer_{bot_id}"),
         InlineKeyboardButton("💰 Request Monetize", callback_data=f"monetize_{bot_id}")],
        [InlineKeyboardButton("🗄️ Manage DB Channel", callback_data=f"db_channel_{bot_id}"),
         InlineKeyboardButton("💎 Switch to Premium", callback_data=f"premium_{bot_id}")],
        [InlineKeyboardButton("👥 User Count", callback_data=f"user_count_{bot_id}")],
        [InlineKeyboardButton("🗑️ Delete Bot (Contact Admin)", callback_data=f"delete_{bot_id}")],
        [InlineKeyboardButton("⬅️ Back to List", callback_data=f"bots_list_page_{current_page}")]
    ]

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )