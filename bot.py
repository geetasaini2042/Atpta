import os, threading
import requests
from pyrogram import Client, filters
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from script import bot,run_flask, run_bot, BOTS_JSON_URL
from common_data import status_user_file, StatusFilter, get_bot_username, BASE_PATH, BOT_TOKEN
BOT_DATA_URL = "https://botdata123.singodiya.tech/all_registered_bot.json"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bots_sync.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ✅ JSON डेटा लोड करने का फ़ंक्शन
def load_bots_data():
    try:
        response = requests.get(BOTS_JSON_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except Exception as e:
        print(f"⚠️ Error loading bots.json: {e}")
        return {}
welcome_buttons = [
        [
            InlineKeyboardButton("➕ Add New Bot", callback_data="add_new_bot"),
            InlineKeyboardButton("🤖 Bots List", callback_data="bots_list_page_1")
        ],
        [InlineKeyboardButton("💎 Switch to Premium", callback_data="switch_to_premium")],
        [InlineKeyboardButton("JOIN CHANNEL", url="https://t.me/BotixHuB_Official")],
        [InlineKeyboardButton("Contact Admin", user_id=6150091802)],
    ]
# ✅ /start कमांड
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user = message.from_user
    text = f"""👋 Hello {user.mention}!

🤖 Welcome to **@BotixHubBot**!
You can manage your bots from here.
"""
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(welcome_buttons),
        disable_web_page_preview=True
    )

# ✅ Filtered callback for "add_new_bot"
import json
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime, timedelta
import pytz
import os, json, requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.on_callback_query(filters.regex("^add_new_bot$"))
async def add_new_bot_cb(client, query):
    user_id = str(query.from_user.id)
    user_plan_file = os.path.join(BASE_PATH, "BOT_DATA", user_id, "user_plans.json")
    #status_user_file = os.path.join(BASE_PATH, "BOT_DATA", "status_users.json")

    # 🇮🇳 India Timezone
    india_tz = pytz.timezone("Asia/Kolkata")
    today = datetime.now(india_tz).date()

    # 🟢 Step 1: Get user's added bot count
    try:
        api_url = "https://botdata123.singodiya.tech/all_registered_bot.json"
        response = requests.get(api_url)
        all_data = response.json()
        used_bots = len(all_data.get(user_id, {}).get("bots", {}))
    except Exception as e:
        return await query.message.edit_text(f"⚠️ Unable to fetch bot info.\nError: {e}")

    # 🟢 Step 2: Load or create user plan data
    if os.path.exists(user_plan_file):
        with open(user_plan_file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    else:
        # Default Free Plan
        plan_data = {
            "owner_id": user_id,
            "plans_active": {
                "basic_free": {"bots": 2, "price": 0, "validity": "lifetime"},
                "paid_plans": []
            },
            "summary": {
                "total_allowed_bots": 2,
                "used_bots": used_bots,
                "remaining_bots": max(0, 2 - used_bots),
                "next_expiry": None
            }
        }

    # 🟢 Step 3: Validate active paid plans (remove expired)
    valid_paid_plans = []
    for plan in plan_data["plans_active"]["paid_plans"]:
        try:
            expiry_date = datetime.strptime(plan["expiry"], "%Y-%m-%d").date()
            if expiry_date >= today:
                valid_paid_plans.append(plan)
        except:
            continue

    # 🟢 Step 4: Calculate allowed bots based on plans
    allowed_bots = plan_data["plans_active"]["basic_free"]["bots"] + sum(
        p["added_bots"] for p in valid_paid_plans
    )
    remaining_bots = allowed_bots - used_bots

    # 🟢 Step 5: If user can still add bots
    if remaining_bots > 0:
        try:
            with open(status_user_file, "r") as f:
                status_data = json.load(f)
        except:
            status_data = {}

        status_data[user_id] = "getting_new_bot_token"

        os.makedirs(os.path.dirname(status_user_file), exist_ok=True)
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)

        instructions = (
            "🆕 **Let's add your new bot!**\n\n"
            "Please send your **Bot Token** here. You can get it from [@BotFather](https://t.me/BotFather).\n\n"
            "**Example:**\n"
            "`123456789:ABCDefGhIJKlmnoPQRstuvWXyz`\n\n"
            "⚠️ Make sure you paste the token exactly — no spaces or extra text."
        )

        cancel_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="back_to_home")]
        ])

        await query.message.edit_text(
            instructions,
            reply_markup=cancel_btn,
            disable_web_page_preview=True
        )
        return

    # 🛑 Step 6: Limit reached or plan expired → show upgrade options
    buy_btns = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 ₹40 - +1 Bot (30 Days)", callback_data="buy_plan_40"),
        ],
        [
            InlineKeyboardButton("💎 ₹80 - +2 Bots (30 Days)", callback_data="buy_plan_80"),
        ],
        [
            InlineKeyboardButton("💎 ₹120 - +3 Bots (30 Days)", callback_data="buy_plan_120"),
        ],
        [
            InlineKeyboardButton("💫 ₹1000 - Unlimited (2 Years)", callback_data="buy_plan_1000")
        ],
        [InlineKeyboardButton("🔙 Back to Home", callback_data="back_to_home")]
    ])

    text = (
        "⚠️ **You’ve reached your bot limit or your plan has expired.**\n\n"
        "Each user gets **2 lifetime free bots.**\n\n"
        "If you want to add more, please upgrade your plan:\n\n"
        "💠 ₹40 → +1 Bot (30 Days)\n"
        "💠 ₹80 → +2 Bots (30 Days)\n"
        "💠 ₹120 → +3 Bots (30 Days)\n"
        "💠 ₹1000 → Unlimited Bots (2 Years)\n\n"
        "**Note:** These are only charges for adding bots. Once a bot is added, it works for lifetime.\n"
        "Premium features for specific bots are separate."
    )

    await query.message.edit_text(text, reply_markup=buy_btns)
import json
import random
import requests
from pyrogram import filters

WEBHOOK_URLS = [
  #  "https://bot-builder-3vlc.onrender.com",
    "https://telegram-bot-builder.onrender.com"
]



@bot.on_message(filters.private & filters.text & StatusFilter("getting_new_bot_token"))
async def receive_new_bot_token(client, message):
    user_id = str(message.from_user.id)
    bot_token = message.text.strip()
    message = await message.reply_text("Please Wait...")

    # ✅ Validate token format
    if ":" not in bot_token or len(bot_token.split(":")[0]) < 5:
        await message.edit_text("⚠️ Invalid token format. Please send a valid bot token (e.g. `123456789:ABCDefGhIjKlmno`).")
        return

    bot_id = bot_token.split(":")[0]

    # ✅ Load remote registered bots list
    try:
        response = requests.get(BOT_DATA_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        await message.edit_text(f"⚠️ Unable to load registered bots list.\nError: `{e}`")
        return

    # ✅ Check if bot already exists in database
    already_registered = False
    for user_info in data.values():
        bots = user_info.get("bots", {})
        if bot_id in bots:
            already_registered = True
            break

    if already_registered:
        await message.edit_text("⚠️ This bot is already registered in the system. Please use a different one.")
        return

    # ✅ Verify token using Telegram API (getMe)
    try:
        tg_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        result = tg_resp.json()
        if not result.get("ok"):
            await message.edit_text("❌ Invalid bot token! Please check it again in @BotFather.")
            return
        bot_info = result["result"]
        username = bot_info.get("username", "Unknown")
    except Exception as e:
        await message.edit_text(f"⚠️ Could not verify token with Telegram.\nError: `{e}`")
        return

    # ✅ Choose a random webhook base
    selected_webhook = random.choice(WEBHOOK_URLS)

    # ✅ Prepare JSON body for /add_bot request
    payload = {
        "bot_token": bot_token,
        "owner_id": int(user_id),
        "is_premium": False,
        "is_monetized": False
    }

    try:
        api_url = f"{selected_webhook}/add_bot"
        r = requests.post(api_url, json=payload, timeout=15)
        btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("Manage Your Bot", callback_data=f"bot_details_{bot_id}")]
    ])
        if r.status_code == 200:
            msg = (
                f"✅ **Bot Added Successfully!**\n\n"
                f"🤖 **Username:** @{username}\n"
                f"🆔 **Bot ID:** `{bot_id}`\n"
                "Your bot has been registered successfully and is ready to use!"
            )
            reply_markup=btn
        else:
            msg = f"❌ Failed to add bot. Server responded with status `{r.status_code}`.\nTry again later."
            reply_markup=None
        send_channel_message(msg, is_button=False, button_text="JOIN CHANNEL", button_type="url", button_data="https://t.me/aibots72")
    except Exception as e:
        msg = f"⚠️ Could not reach webhook server.\nError: `{e}`"

    # ✅ Clear user status
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    await message.edit_text(msg, disable_web_page_preview=True,reply_markup= reply_markup)
# New global variable to track pages per user (in-memory, can be replaced with DB)
user_pages = {}  # {user_id: current_page}

@bot.on_callback_query(filters.regex("^back_to_home$"))
async def back_home_cb(client, query):
    message = query.message
    #await start_cmd(client, query.message)
    user = message.from_user
    user_id = str(message.from_user.id)
    #user_id = 
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)
    text = f"""👋 Hello {user.mention}!

🤖 Welcome to **@BotixHubBot**!
You can manage your bots from here.
"""
    await query.message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(welcome_buttons),
        disable_web_page_preview=True
    )

    
    
from datetime import datetime, timedelta
import pytz
import os, json
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# Required imports
from datetime import datetime, timedelta
import pytz
import os
import json
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Assumptions:
# - `bot` and `BASE_PATH` are defined in your main bot file.
# - buy_plan_callback that handles buy_plan_40 / buy_plan_80 / buy_plan_120 / 
#   already exists (it saves to BOT_DATA/{user_id}/user_plans.json).
# - This handler only reads/edits the message and directs the user to buy/extend.

@bot.on_callback_query(filters.regex("^switch_to_premium$"))
async def switch_to_premium_cb(client, query):
    import aiohttp

    user_id = str(query.from_user.id)
    india_tz = pytz.timezone("Asia/Kolkata")
    today = datetime.now(india_tz).date()

    # Path to user's plan file
    user_plan_file = os.path.join(BASE_PATH, "BOT_DATA", user_id, "user_plans.json")

    # 🟡 Fetch used bots count from online JSON
    used_bots = 0
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://botdata123.singodiya.tech/all_registered_bot.json") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if user_id in data:
                        used_bots = len(data[user_id].get("bots", {}))
    except Exception as e:
        print("BotData fetch error:", e)

    # ✅ Load local user plan file
    if os.path.exists(user_plan_file):
        try:
            with open(user_plan_file, "r", encoding="utf-8") as f:
                user_plan = json.load(f)
        except Exception as e:
            user_plan = None
    else:
        user_plan = None

    # ✅ If user already has a plan
    if user_plan:
        summary = user_plan.get("summary", {})
        total_allowed = summary.get("total_allowed_bots", None)
        remaining1 = int(total_allowed) - int(used_bots) #summary.get("remaining_bots", None)
        if remaining1 < 0:
          remaining = 0
        elif total_allowed > 9999:
          total_allowed = "Unlimited"
          remaining = "Unlimited"
        else:
          remaining = remaining1
          
        next_expiry = summary.get("next_expiry") or user_plan.get("expiry")

        expired = False
        expiry_display = next_expiry or "Unknown"
        try:
            if next_expiry:
                expiry_date = datetime.strptime(next_expiry, "%Y-%m-%d").date()
                expired = today > expiry_date
        except:
            expired = False

        paid_plans = user_plan.get("plans_active", {}).get("paid_plans", []) or user_plan.get("plans", [])
        if not paid_plans:
            plans_text = "No purchased paid plans found."
            text = (
                "💎 **Premium Plans**\n\n"
                "You get 2 bots free for lifetime.\n\n"
                "Choose a plan to increase your bot limit:\n"
                "• 💰 ₹40 → +1 Bot (30 Days)\n"
                "• 💰 ₹80 → +2 Bots (30 Days)\n"
                "• 💰 ₹120 → +3 Bots (30 Days)\n"
                "• 💰 ₹1000 → Unlimited Bots (2 Years)\n\n"
                "📌 **Note:** This fee only covers adding bots. Each added bot remains functional forever. "
                "Premium features of individual bots are separate."
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 ₹40 Plan", callback_data="buy_plan_40")],
                [InlineKeyboardButton("💰 ₹80 Plan", callback_data="buy_plan_80")],
                [InlineKeyboardButton("💰 ₹120 Plan", callback_data="buy_plan_120")],
                [InlineKeyboardButton("💎 ₹1000 Unlimited", callback_data="buy_plan_1000")],
                [InlineKeyboardButton("⬅️ Back", callback_data="back_to_home")]
            ])

            await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
            return
        else:
            lines = []
            for p in paid_plans:
                price = p.get("price", "N/A")
                bots = p.get("added_bots", p.get("bots", "N/A"))
                days = p.get("days", "N/A")
                purchased_on = p.get("purchased_on", p.get("start_date", "Unknown"))
                expiry = p.get("expiry", "Unknown")
                lines.append(f"₹{price} • +{bots} Bots • {days} days • bought: {purchased_on} • exp: {expiry}")
            plans_text = "\n".join(lines)

        text = (
            "💎 **Your Premium Details**\n\n"
            f"👤 User ID: `{user_id}`\n\n"
            f"📦 Allowed Bots: {total_allowed if total_allowed is not None else 'Unknown'}\n"
            f"🤖 Used Bots: {used_bots}\n"
            f"🟢 Remaining Slots: {remaining if remaining is not None else (total_allowed - used_bots if total_allowed else 'Unknown')}\n"
            f"📅 Next Expiry: {expiry_display}\n"
            f"⏳ Status: {'❌ Expired' if expired else '✅ Active'}\n\n"
            "**Purchased Plans:**\n"
            f"{plans_text}\n\n"
            "🔔 **Note:** This charge only covers adding bot slots. Once a bot is added, it remains active for lifetime.\n"
            "✨ Specific bot premium features must be purchased separately per bot."
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🕓 Extend Validity / Increase Limit", callback_data="extend_premium")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_home")]
        ])

        await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        return

    # 🟢 If user is not premium
    text = (
        "💎 **Premium Plans**\n\n"
        "You get 2 bots free for lifetime.\n\n"
        "Choose a plan to increase your bot limit:\n"
        "• 💰 ₹40 → +1 Bot (30 Days)\n"
        "• 💰 ₹80 → +2 Bots (30 Days)\n"
        "• 💰 ₹120 → +3 Bots (30 Days)\n"
        "• 💰 ₹1000 → Unlimited Bots (2 Years)\n\n"
        "📌 **Note:** This fee only covers adding bots. Each added bot remains functional forever. "
        "Premium features of individual bots are separate."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 ₹40 Plan", callback_data="buy_plan_40")],
        [InlineKeyboardButton("💰 ₹80 Plan", callback_data="buy_plan_80")],
        [InlineKeyboardButton("💰 ₹120 Plan", callback_data="buy_plan_120")],
        [InlineKeyboardButton("💎 ₹1000 Unlimited", callback_data="buy_plan_1000")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_home")]
    ])

    await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
# ---- extend_premium handler: show same buy options but labeled as "Extend / Increase"
@bot.on_callback_query(filters.regex("^extend_premium$"))
async def extend_premium_cb(client, query):
    text = (
        "🕓 **Extend Validity / Increase Limit**\n\n"
        "Choose one of the following to extend your current plan or increase bot slots.\n\n"
        "Selections will be appended to your existing paid plans (cumulative), and expiry will be calculated in IST.\n\n"
        "• 💰 ₹40 → +1 Bot (30 Days)\n"
        "• 💰 ₹80 → +2 Bots (30 Days)\n"
        "• 💰 ₹120 → +3 Bots (30 Days)\n"
        "• 💰 ₹1000 → Unlimited Bots (2 Years)\n\n"
        "📌 Note: These are charges only for adding slots/validity. Bot-specific premium features are separate."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 ₹40 - Add +1 (30d)", callback_data="buy_plan_40")],
        [InlineKeyboardButton("💰 ₹80 - Add +2 (30d)", callback_data="buy_plan_80")],
        [InlineKeyboardButton("💰 ₹120 - Add +3 (30d)", callback_data="buy_plan_120")],
        [InlineKeyboardButton("💎 ₹1000 - Unlimited (2y)", callback_data="buy_plan_1000")],
        [InlineKeyboardButton("⬅️ Back", callback_data="switch_to_premium")]
    ])

    await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    

def send_channel_message(text, is_button=False, button_text="JOIN CHANNEL", button_type="url", button_data="https://t.me/aibots72"):
    """
    किसी Telegram चैनल पर संदेश और inline बटन भेजता है।
    """
    bot_token = BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # Inline keyboard JSON
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": button_text, button_type: button_data}
            ]
        ]
    }
    if is_button:
      payload = {
        "chat_id": -1003223758572,   # Example: "@my_channel" या "-1001234567890"
        "text": text,
        "reply_markup": json.dumps(reply_markup),
        "parse_mode": "HTML"
      }
    else:
      payload = {
        "chat_id": -1003223758572,   # Example: "@my_channel" या "-1001234567890"
        "text": text,
        "parse_mode": "HTML"
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("✅ संदेश सफलतापूर्वक भेजा गया!")
        return response.json()
    else:
        print("❌ भेजने में त्रुटि:", response.text)
        return None

import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 📨 Channel Message भेजने का फ़ंक्शन

# 🎯 Callback Handler — Buy Plan Click
@bot.on_callback_query(filters.regex("^buy_plan_"))
async def buy_plan_callback(client, query):
    user = query.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    plan_key = query.data  # e.g. "buy_plan_40"
    plan_price = plan_key.replace("buy_plan_", "")

    # ✅ Channel Message बनाना
    channel_text = (
        f"💳 <b>New Plan Purchase Request</b>\n\n"
        f"👤 User: {username} (<code>{user_id}</code>)\n"
        f"🪙 Selected Plan: ₹{plan_price}\n\n"
        f"Admin can verify and approve below 👇"
    )

    callback_for_admin = f"sell_plan_{plan_price}:{user_id}"

    # 📨 Channel पर भेजें
  
    send_channel_message(channel_text, is_button=True, button_text="CONFIRM REQUEST", button_type="callback_data", button_data=callback_for_admin)

    # 👤 User को जानकारी दिखाएँ
    back_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Upgrade Now", url="https://t.me/mr_singodiyabot")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_home")]
    ])

    await query.message.edit_text(
        "Currently automatic payment system is not supported.\n"
        "It will be available soon...\n\n"
        "To buy a Premium Plan please contact Admin 👇\n@mr_singodiyabot",
        reply_markup=back_btn
    )

import os
import json
import uuid
from datetime import datetime, timedelta
import pytz
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@bot.on_callback_query(filters.regex("^sell_plan_"))
async def sell_plan_callback(client, query):
    india_tz = pytz.timezone("Asia/Kolkata")
    today = datetime.now(india_tz).date()

    # 🔍 Callback से data निकालना
    data_parts = query.data.split(":")
    plan_key = data_parts[0]          # e.g. "sell_plan_40"
    user_id = data_parts[1] if len(data_parts) > 1 else None

    if not user_id:
        return await query.answer("❌ User ID नहीं मिला", show_alert=True)

    # 📦 Plan विवरण
    plan_prices = {
        "sell_plan_40": {"price": 40, "added_bots": 1, "days": 30},
        "sell_plan_80": {"price": 80, "added_bots": 2, "days": 30},
        "sell_plan_120": {"price": 120, "added_bots": 3, "days": 30},
        "sell_plan_1000": {"price": 1000, "added_bots": 9999, "days": 730}
    }

    if plan_key not in plan_prices:
        return await query.answer("❌ Invalid Plan Key", show_alert=True)

    plan = plan_prices[plan_key]
    expiry = today + timedelta(days=plan["days"])
    unique_id = str(uuid.uuid4())[:8]   # हर plan के लिए छोटा unique ID

    # 📂 File Path
    user_plan_file = os.path.join(BASE_PATH, "BOT_DATA", user_id, "user_plans.json")
    os.makedirs(os.path.dirname(user_plan_file), exist_ok=True)

    # 🔄 Load या Create JSON
    if os.path.exists(user_plan_file):
        with open(user_plan_file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    else:
        plan_data = {
            "owner_id": user_id,
            "plans_active": {
                "basic_free": {"bots": 2, "price": 0, "validity": "lifetime"},
                "paid_plans": []
            },
            "summary": {
                "total_allowed_bots": 2,
                "used_bots": 0,
                "remaining_bots": 2,
                "next_expiry": None
            }
        }

    # ⏳ Expired Plans हटाना
    valid_paid_plans = []
    for p in plan_data["plans_active"]["paid_plans"]:
        try:
            exp_date = datetime.strptime(p["expiry"], "%Y-%m-%d").date()
            if exp_date >= today:
                valid_paid_plans.append(p)
        except:
            continue

    # 🆕 New Plan जोड़ना
    new_plan = {
        "plan_id": unique_id,
        "price": plan["price"],
        "added_bots": plan["added_bots"],
        "days": plan["days"],
        "purchased_on": str(today),
        "expiry": str(expiry)
    }
    valid_paid_plans.append(new_plan)

    plan_data["plans_active"]["paid_plans"] = valid_paid_plans
    total_bots = plan_data["plans_active"]["basic_free"]["bots"] + sum(p["added_bots"] for p in valid_paid_plans)
    plan_data["summary"]["total_allowed_bots"] = total_bots
    plan_data["summary"]["next_expiry"] = str(max(datetime.strptime(p["expiry"], "%Y-%m-%d").date() for p in valid_paid_plans))

    # 💾 Save File
    with open(user_plan_file, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2)

    # ✅ User को Plan Activated Message भेजना
    confirm_text = (
        f"🎉 **Plan Activated Successfully!**\n\n"
        f"🧾 **Plan ID:** `{unique_id}`\n"
        f"💰 **Price:** ₹{plan['price']}\n"
        f"🤖 **Added Bots:** +{plan['added_bots']}\n"
        f"📅 **Validity:** {plan['days']} Days\n"
        f"🗓️ **Expiry Date:** {expiry}\n\n"
        f"_Note: Once added, bot remains lifetime active._"
    )

    user_msg = await client.send_message(int(user_id), confirm_text)

    # 🟢 Admin को Cancel वाला बटन दिखाना
    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Activation", callback_data=f"cancel_plan:{unique_id}:{user_id}:{user_msg.id}")]
    ])

    await query.message.edit_text(
        f"✅ Plan Activated Successfully!\n\n👤 User ID: `{user_id}`\n💰 ₹{plan['price']} | +{plan['added_bots']} bots\n🆔 Plan ID: `{unique_id}`",
        reply_markup=cancel_btn
    )

    await query.answer("✅ User Plan Activated & Notified!", show_alert=True)

@bot.on_callback_query(filters.regex("^cancel_plan"))
async def cancel_plan_callback(client, query):
    try:
        _, plan_id, user_id, msg_id = query.data.split(":")
    except ValueError:
        return await query.answer("❌ Invalid cancel data", show_alert=True)

    user_plan_file = os.path.join(BASE_PATH, "BOT_DATA", user_id, "user_plans.json")

    if not os.path.exists(user_plan_file):
        return await query.answer("⚠️ User Plan File Not Found", show_alert=True)

    with open(user_plan_file, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    paid_plans = plan_data.get("plans_active", {}).get("paid_plans", [])
    canceled_plan = None

    # 🔍 Remove Plan by ID and keep canceled plan details
    new_paid_plans = []
    for p in paid_plans:
        if p.get("plan_id") == plan_id:
            canceled_plan = p
        else:
            new_paid_plans.append(p)

    if not canceled_plan:
        return await query.answer("❌ Plan ID Not Found", show_alert=True)

    plan_data["plans_active"]["paid_plans"] = new_paid_plans

    # 🧮 अब summary को फिर से अपडेट करें
    basic_bots = plan_data["plans_active"]["basic_free"].get("bots", 2)
    total_paid_bots = sum(p.get("added_bots", 0) for p in new_paid_plans)
    total_bots = basic_bots + total_paid_bots

    # अगला expiry निकालना (अगर कोई paid plan बचा है)
    if new_paid_plans:
        next_expiry = str(
            max(datetime.strptime(p["expiry"], "%Y-%m-%d").date() for p in new_paid_plans)
        )
    else:
        next_expiry = None

    # ✅ Summary अपडेट करें
    plan_data["summary"].update({
        "total_allowed_bots": total_bots,
        "remaining_bots": total_bots - plan_data["summary"].get("used_bots", 0),
        "next_expiry": next_expiry
    })

    # 💾 Save after removal + summary update
    with open(user_plan_file, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2)

    # 🗑️ User को भेजा गया Activated Message Delete करें
    try:
        await client.delete_messages(int(user_id), int(msg_id))
    except Exception as e:
        print(f"⚠️ Error deleting user message: {e}")

    # 🟢 Canceled Plan Details निकालना
    plan_price = canceled_plan.get("price", "N/A")
    added_bots = canceled_plan.get("added_bots", "N/A")
    expiry = canceled_plan.get("expiry", "N/A")

    # 🔁 Channel Message दोबारा Update करें
    re_confirm_btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💰 GOT PAYMENT SUCCESSFULLY",
                callback_data=f"sell_plan_{plan_price}:{user_id}"
            )
        ]
    ])

    await query.message.edit_text(
        f"❌ **Plan Activation Canceled!**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"🆔 **Plan ID:** `{plan_id}`\n"
        f"💰 **Price:** ₹{plan_price}\n"
        f"🤖 **Bots Added:** {added_bots}\n"
        f"📅 **Expiry:** {expiry}\n\n"
        f"🔄 You can confirm again below 👇",
        reply_markup=re_confirm_btn
    )

    await query.answer("✅ Plan canceled, summary updated & user message deleted!", show_alert=True)
import bot_details
import revoke
import Admins, db_channel , payment
@bot.on_callback_query()
async def unknown_cb(client, query):
    await query.answer("Comming Soon...", show_alert=True)
    

    
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
