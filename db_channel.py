import json
import base64
import re
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from onlyfunctions import get_webhook_base_url, get_bot_token_by_id
from common_data import status_user_file, StatusFilter, get_bot_username
from pyrogram.filters import Filter
from script import bot
# 상태 prefix 사용
STATUS_PREFIX_DB = "setting_db_channel_for_"

# ---------------- Show current DB channel / options ----------------
@bot.on_callback_query(filters.regex(r"^db_channel_(\d+)$"))
async def db_channel_cb(client, query):
    bot_id = query.data.split("_")[-1]
    await query.message.edit_text("⏳ Please wait... Fetching database channel information...")

    # fetch webhook & token
    webhook_base_url = get_webhook_base_url(bot_id)
    bot_token = get_bot_token_by_id(bot_id)
    if webhook_base_url == "N/A" or bot_token == "N/A":
        await query.message.edit_text("⚠️ Unable to fetch bot info. Please try again later.")
        return

    additional_url = f"{webhook_base_url}/auth{bot_token}/ADDITIONAL_DATA.json"
    try:
        r = requests.get(additional_url, timeout=10)
        data = r.json()
    except Exception as e:
        await query.message.edit_text(f"⚠️ Failed to load ADDITIONAL_DATA.json: `{e}`")
        return

    # If file not found or error -> show Add Database Channel
    if "error" in data:
        text = (
            f"📂 **Database Channel:** Not configured for Bot `{bot_id}`.\n\n"
            "You can add a Database Channel to store files. Private channels are recommended."
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Database Channel", callback_data=f"add_db_channel_{bot_id}")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"bot_details_{bot_id}")]
        ])
        await query.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
        return

    # If present, show channel id and try to show channel details via Telegram getChat
    print(data)
    data = data.get("data")
    print("÷=/_/==÷÷")
    print(data)
    file_channel_id = data.get("FILE_CHANNEL_ID")
    channel_info_text = f"📂 **Database Channel ID:** `{file_channel_id}`\n"

    # Try to fetch channel details using bot token
    try:
        tg_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={file_channel_id}", timeout=10)
        tg_json = tg_resp.json()
        if tg_json.get("ok"):
            res = tg_json["result"]
            title = res.get("title") or f"Channel {file_channel_id}"
            username = res.get("username")
            channel_info_text += f"📝 **Title:** {title}\n"
            if username:
                channel_info_text += f"🔗 **Username:** @{username}\n"
            channel_info_text += f"\nYou can change the Database Channel below."
        else:
            channel_info_text += "\n⚠️ Could not fetch channel details (maybe bot is not a member)."
    except Exception as e:
        channel_info_text += f"\n⚠️ Error fetching channel details: `{e}`"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Change Database Channel", callback_data=f"add_db_channel_{bot_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"bot_details_{bot_id}")]
    ])

    await query.message.edit_text(channel_info_text, reply_markup=kb, disable_web_page_preview=True)

pending_db_channel_msgs = {}

# ---------------- Start Add / Change flow ----------------
@bot.on_callback_query(filters.regex(r"^add_db_channel_(\d+)$"))
async def add_db_channel_start_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)

    # Save status
    try:
        with open(status_user_file, "r") as f:
            status = json.load(f)
    except:
        status = {}
    status[user_id] = f"{STATUS_PREFIX_DB}{bot_id}"
    with open(status_user_file, "w") as f:
        json.dump(status, f, indent=2)

    instructions = (
        "➕ **Add / Change Database Channel**\n\n"
        "Please do **one** of the following:\n"
        "1. Forward any message from the CHANNEL you want to set as Database Channel.\n"
        "2. Or send the channel ID (for public channels use numeric ID or @username; for private channels use the numeric ID like `-1001234567890`).\n\n"
        "Recommendation: Use a private channel where only the bot and trusted admins are members.\n\n"
        "When you forward a message, make sure it was originally posted in that channel (forward_from_chat will be present).\n\n"
        "Press ❌ Cancel to abort."
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_set_db_{bot_id}")]
    ])

    #await query.message.edit_text(instructions, reply_markup=kb, disable_web_page_preview=True)
    msg = await query.message.edit_text(instructions,reply_markup=kb, disable_web_page_preview=True)
    pending_db_channel_msgs[query.from_user.id] = {
       "bot_id": bot_id,
       "message_id": msg.id
      }


# ---------------- Cancel add/change ----------------
@bot.on_callback_query(filters.regex(r"^cancel_set_db_(\d+)$"))
async def cancel_set_db_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)
    try:
        with open(status_user_file, "r") as f:
            status = json.load(f)
    except:
        status = {}
    status[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(status, f, indent=2)

    await query.message.edit_text("❌ Database channel setup cancelled.", reply_markup=None)


# ---------------- Handler to receive forwarded channel message or direct id ----------------
@bot.on_message(filters.private & StatusFilter(STATUS_PREFIX_DB))
async def set_db_channel_receive(client, message):
    user_id = str(message.from_user.id)

    # ✅ पहले पुराना "Add / Change Database Channel" वाला msg delete करें
    user_pending = pending_db_channel_msgs.get(message.from_user.id)
    if user_pending:
        try:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=user_pending["message_id"]
            )
        except Exception:
            pass  # ignore if already deleted
        del pending_db_channel_msgs[message.from_user.id]
    mer= await message.reply_text("Please Wait...")
    pending_db_channel_msgs[message.from_user.id] = {"message_id": mer.id}
    # ✅ Load status -> get bot_id
    try:
        with open(status_user_file, "r") as f:
            status = json.load(f)
            s = status.get(user_id, "")
            if s.startswith(STATUS_PREFIX_DB):
                bot_id = s.replace(STATUS_PREFIX_DB, "")
            else:
                bot_id = None
    except Exception:
        await mer.edit_text("⚠️ Could not read session. Try again.")
        return

    if not bot_id:
        await mer.edit_text("⚠️ Bot ID not found in session. Please restart.")
        return
    back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back" , callback_data=f"db_channel_{bot_id}")]
    ])
    # Determine candidate channel id either from forwarded message or direct text
    candidate_chat_id = None

    # If forwarded from a chat (channel/group), forward_from_chat will be present
    forwarded_chat = getattr(message, "forward_from_chat", None)
    forward_sender_name = getattr(message, "forward_sender_name", None)
    forwarded_from = getattr(message, "forward_from", None)

    if forwarded_chat and not forwarded_from and not forward_sender_name:
        # Consider this as forwarded from a channel/group
        # forwarded_chat.id should be chat id
        candidate_chat_id = forwarded_chat.id
    else:
        # Try direct ID or username in message text
        text = (message.text or "").strip()
        # Accept formats: -1001234567890 OR digits OR @username
        if re.fullmatch(r"-?100?\d{5,}", text) or re.fullmatch(r"\d{5,}", text) or text.startswith("@"):
            candidate_chat_id = text
        else:
            await mer.edit_text(
                "⚠️ Please forward a message from the channel OR send the channel ID/username.\n"
                "Example IDs: `-1001234567890` or `123456789` or `@channelusername`."
            )
            return

    # Fetch webhook and bot token
    webhook_base_url = get_webhook_base_url(bot_id)
    bot_token = get_bot_token_by_id(bot_id)
    if webhook_base_url == "N/A" or bot_token == "N/A":
        await mer.edit_text("⚠️ Unable to fetch bot info. Please try later.")
        # clear status
        try:
            with open(status_user_file, "r") as f:
                st = json.load(f)
        except:
            st = {}
        st[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(st, f, indent=2)
        return

    # Verify candidate chat via Telegram getChat
    try:
        tg_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={candidate_chat_id}", timeout=10)
        tg_json = tg_resp.json()
        #print(tg_json)
        bot_username = get_bot_username(bot_id)
        if not tg_json.get("ok"):
            await mer.edit_text(f"⚠️ Could not verify the provided channel ID/username. Make sure you bot @{bot_username} is a member of that channel or the ID is correct.")
            return
            # clear status
            with open(status_user_file, "r") as f:
                st = json.load(f)
            st[user_id] = ""
            with open(status_user_file, "w") as f:
                json.dump(st, f, indent=2)
            return
        chat_info = tg_json["result"]
        chat_type = chat_info.get("type", "")
        # Accept channels and supergroups
        if chat_type not in ("channel", "supergroup"):
            await mer.edit_text("⚠️ The provided chat is not a channel or supergroup. Please provide a channel/supergroup.")
            return
            st = {}
            try:
                with open(status_user_file, "r") as f:
                    st = json.load(f)
            except:
                st = {}
            st[user_id] = ""
            with open(status_user_file, "w") as f:
                json.dump(st, f, indent=2)
            return

        # Normalize chat id
        confirmed_chat_id = chat_info.get("id")
        title = chat_info.get("title", str(confirmed_chat_id))
    except Exception as e:
        await mer.edit_text(f"⚠️ Failed to verify channel: `{e}`")
        # clear status
        with open(status_user_file, "r") as f:
            st = json.load(f)
        st[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(st, f, indent=2)
        return

    # Try to send a test message to channel using bot token
    test_text = "🔔 Database channel verification message. If you see this, the channel is configured correctly."
    try:
        send_resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": confirmed_chat_id, "text": test_text},
            timeout=10
        )
        send_json = send_resp.json()
        if not send_json.get("ok"):
            await mer.edit_text(f"❌ Failed to send test message to the channel. Make sure your bot @{bot_username} is an admin/member of the channel and it accepts messages.",reply_markup= back)
            # clear status
            with open(status_user_file, "r") as f:
                st = json.load(f)
            st[user_id] = ""
            with open(status_user_file, "w") as f:
                json.dump(st, f, indent=2)
            return
    except Exception as e:
        await mer.edit_text(f"❌ Error sending test message: `{e}`")
        # clear status
        with open(status_user_file, "r") as f:
            st = json.load(f)
        st[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(st, f, indent=2)
        return

    # If test message succeeded -> POST to server to update ADDITIONAL_DATA.json
    additional_url = f"{webhook_base_url}/auth{bot_token}/ADDITIONAL_DATA.json"
    payload = {"FILE_CHANNEL_ID": confirmed_chat_id}
    try:
        post_resp = requests.post(additional_url, json=payload, timeout=12)
        if post_resp.status_code in (200, 201):
            await mer.edit_text(f"✅ Database channel set successfully: **{title}** (`{confirmed_chat_id}`).",reply_markup= back)
        else:
            await mer.edit_text(f"❌ Failed to update server. Status code: {post_resp.status_code}",reply_markup= back)
    except Exception as e:
        await mer.edit_text(f"❌ Failed to update server: `{e}`",reply_markup= back)

    # Clear status
    try:
        with open(status_user_file, "r") as f:
            st = json.load(f)
    except:
        st = {}
    st[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(st, f, indent=2)