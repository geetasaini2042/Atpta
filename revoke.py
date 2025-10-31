import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.filters import Filter
import os
from common_data import status_user_file, StatusFilter, get_bot_username
from script import bot
from bot_details import bot_details_cb
# ---------- Status Filter ----------

# ---------- Revoke Bot Handler ----------
@bot.on_callback_query(filters.regex(r"^revoke_(\d+)$"))
async def revoke_bot_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)

    # ✅ Save user status
    try:
        if os.path.exists(status_user_file):
            with open(status_user_file, "r") as f:
                status_data = json.load(f)
        else:
            status_data = {}
    except:
        status_data = {}

    status_data[user_id] = f"getting_revoked_new_token_for_{bot_id}"
    username = get_bot_username(bot_id)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # ✅ Instructions to user
    instructions = (
        f"🔹 You are about to **revoke the token** for Bot ID `{bot_id}`.\n\n"
        "Please follow these steps carefully:\n"
        "1. Open your BotFather in Telegram.\n"
        f"2. Select your bot @{username}.\n"
        "3. Use the /revoke command to revoke the current token.\n"
        "4. Use /token to generate a **new token**.\n\n"
        "Once you have the new token, send it here in the chat."
    )

    await query.message.edit_text(
        instructions,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancel", callback_data=f"cancel_revoke_{bot_id}")]
        ])
    )
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@bot.on_callback_query(filters.regex(r"^cancel_revoke_(\d+)$"))
async def cancel_and_come_onbot_detail(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)

    # ✅ Clear user status in status.json
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    if user_id in status_data:
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)

    # 🔹 Fetch bot details again
    # Assuming you already have the function bot_details_cb logic separated
    # If not, we can call the same code inline here:

    # For simplicity, we reuse the same callback logic
    # This will reopen the bot details page
    from functools import partial
    query.data = f"bot_details_{bot_id}"  # modify callback data
    await bot_details_cb(client, query)  # call existing bot_details handler
import json
import re
import requests
from pyrogram import filters
from pyrogram.types import Message

@bot.on_message(filters.private & filters.text & StatusFilter("getting_revoked_new_token_for_"))
async def receive_new_token(client, message: Message):
    user_id = str(message.from_user.id)
    new_token = message.text.strip()

    # ✅ Validate bot token format (digits:alphanumeric)
    if not re.fullmatch(r"\d{6,}:[\w-]+", new_token):
        await message.reply_text("⚠️ Invalid bot token format. Please send the token exactly like `123456789:ABCDEF`.")
        return

    # Extract bot_id from status
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
            status = status_data.get(user_id, "")
            if status.startswith("getting_revoked_new_token_for_"):
                bot_id = status.replace("getting_revoked_new_token_for_", "")
            else:
                bot_id = None
    except:
        await message.reply_text("⚠️ Could not process your status. Please try again.")
        return

    if not bot_id:
        await message.reply_text("⚠️ Bot ID not found in your session. Please try again.")
        return

    # ✅ Check token with Telegram API getMe using requests
    try:
        resp = requests.get(f"https://api.telegram.org/bot{new_token}/getMe", timeout=10)
        data = resp.json()
        if not data.get("ok"):
            await message.reply_text("⚠️ This token is invalid or expired. Please double-check it.")
            return
        token_username = data["result"]["username"]
    except Exception as e:
        await message.reply_text(f"⚠️ Failed to validate token: {e}")
        return

    # ✅ Check username match with original bot
    original_username = get_bot_username(bot_id)
    if token_username != original_username:
        await message.reply_text(
            f"⚠️ The username of this token (@{token_username}) does not match your bot's original username (@{original_username}).\n"
            "This seems to be a new bot token. Please create a new bot instead."
        )
        return

    # ✅ Get webhook_base_url from main bot data
    try:
        resp = requests.get("https://botdata123.singodiya.tech/all_registered_bot.json", timeout=10)
        bots_data = resp.json()
        webhook_base_url = None
        for user_info in bots_data.values():
            for b_id, b in user_info.get("bots", {}).items():
                if b_id == bot_id:
                    webhook_base_url = b.get("webhook_base_url")
                    print(webhook_base_url)
                    break
            if webhook_base_url:
                break
        if not webhook_base_url:
            await message.reply_text("⚠️ Could not fetch webhook base URL for your bot. Please try later.")
            return
    except Exception as e:
        await message.reply_text(f"⚠️ Error fetching bot data: {e}")
        return

    # ✅ Send POST request to add_bot
    post_url = f"{webhook_base_url}/add_bot"
    payload = {
        "bot_token": new_token,
        "owner_id": int(user_id)
    }
    try:
        r = requests.post(post_url, json=payload, timeout=10)
        if r.status_code == 200:
            await message.reply_text(f"✅ New token successfully updated for your bot (@{token_username}).")
        else:
            await message.reply_text(f"⚠️ Failed to update token. Server responded with status code {r.status_code}.")
    except Exception as e:
        await message.reply_text(f"⚠️ Failed to send request: {e}")

    # ✅ Clear user status
    status_data[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)