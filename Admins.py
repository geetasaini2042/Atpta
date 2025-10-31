import requests
import base64
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from onlyfunctions import get_webhook_base_url, get_bot_token_by_id
from script import bot
from common_data import StatusFilter
import json
import base64
import requests
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from onlyfunctions import get_webhook_base_url, get_bot_token_by_id, is_premium_active
from common_data import status_user_file
import re

@bot.on_callback_query(filters.regex(r"^manage_admins_(\d+)$"))
async def manage_admins_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = query.from_user.id

    # Step 1: Show waiting message
    await query.message.edit_text("⏳ Please wait... Fetching admin details...")

    # Step 2: Fetch webhook_base_url and bot_token
    webhook_base_url = get_webhook_base_url(bot_id)
    bot_token = get_bot_token_by_id(bot_id)

    if webhook_base_url == "N/A" or bot_token == "N/A":
        await query.message.edit_text("⚠️ Unable to fetch bot information. Please try again later.")
        return

    # Step 3: Fetch ADMINS.json
    admins_url = f"{webhook_base_url}/auth{bot_token}/ADMINS.json"
    try:
        res = requests.get(admins_url, timeout=10)
        data = res.json()
    except Exception as e:
        await query.message.edit_text(f"⚠️ Failed to load admin data.\nError: `{e}`")
        return

    # Step 4: Handle “File not found” case
    if "error" in data:
        text = (
            f"🤖 **Manage Admins for Bot ID:** `{bot_id}`\n\n"
            f"📂 No admins found yet for this bot.\n"
            f"You can add the first admin now."
        )
        buttons = [
            [InlineKeyboardButton("➕ Add New Admin", callback_data=f"add_admin_{bot_id}")],
            [InlineKeyboardButton("💎 Get Premium", callback_data="premium_info")],
            [InlineKeyboardButton("⬅️ Back", callback_data=f"bot_details_{bot_id}")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Step 5: Extract IDs
    admin_data = data.get("data", {})
    owners = admin_data.get("owner", [])
    admins = admin_data.get("admin", [])

    all_ids = owners + admins

    # Step 6: Get usernames via Telegram API
    id_name_map = {}
    for uid in all_ids:
        try:
            r = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={uid}", timeout=10)
            info = r.json()
            if info.get("ok"):
                user_info = info.get("result", {})
                first_name = user_info.get("first_name", "")
                last_name = user_info.get("last_name", "")
                full_name = f"{first_name} {last_name}".strip() or f"User {uid}"
                id_name_map[uid] = full_name
            else:
                id_name_map[uid] = f"User {uid}"
        except Exception:
            id_name_map[uid] = f"User {uid}"

    # Step 7: Check Premium Status
    try:
        is_premium = is_premium_active(bot_id)
    except:
        is_premium = False

    # Step 8: Build Admin List
    text_lines = [f"🤖 **Manage Admins for Bot ID:** `{bot_id}`\n"]
    text_lines.append(f"👑 **OWNER:**")
    for oid in owners:
        text_lines.append(f"   • {id_name_map.get(oid, str(oid))}")

    text_lines.append("\n👮 **ADMINS:**")
    if admins:
        for aid in admins:
            text_lines.append(f"   • {id_name_map.get(aid, str(aid))}")
    else:
        text_lines.append("   • None")

    # Step 9: Buttons — Add Admin limit logic
    max_admins = 5 if is_premium else 2
    buttons = []

    if len(admins) < max_admins:
        buttons.append([InlineKeyboardButton("➕ Add New Admin", callback_data=f"add_admin_{bot_id}")])
    else:
        buttons.append([InlineKeyboardButton("⚠️ Admin Limit Reached", callback_data="none")])
    buttons.append([InlineKeyboardButton("➖️ Dismiss an admin", callback_data=f"remove_admin_{bot_id}")])
    buttons.append([InlineKeyboardButton("💎 Get Premium", callback_data="premium_info")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"bot_details_{bot_id}")])

    text = "\n".join(text_lines)

    # Step 10: Edit message with final data
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )
    

STATUS_PREFIX = "adding_admin_for_"

# ----------------- Step A: callback to start add-admin flow -----------------
@bot.on_callback_query(filters.regex(r"^add_admin_(\d+)$"))
async def add_admin_start_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)

    # Save status so next forwarded message is captured
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = f"{STATUS_PREFIX}{bot_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    instructions = (
        "➕ **Add New Admin — Forward a user's message**\n\n"
        "Please either forward a message from the private user you want to add, "
        "or send the user's numeric **Telegram ID** (digits only).\n\n"
        "• Make sure you forward a message that was originally sent by a **private user** (not from a channel or group).\n"
        "• After you forward, I will validate and add that user to the bot's admin list if allowed.\n\n"
        "Press **Cancel** to abort."
    )

    cancel_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_add_admin_{bot_id}")]
    ])

    msg = await query.message.edit_text(instructions, reply_markup=cancel_kb, disable_web_page_preview=True)
    pending_get_admin_msgs[query.from_user.id] = {
       "bot_id": bot_id,
       "message_id": msg.id
      }

pending_get_admin_msgs = {}
# ----------------- Optional: cancel handler -----------------
@bot.on_callback_query(filters.regex(r"^cancel_add_admin_(\d+)$"))
async def cancel_add_admin_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)

    # Clear status
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)
    back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back" , callback_data=f"manage_admins_{bot_id}")]
    ])
    await query.message.edit_text("❌ Add admin process cancelled.", reply_markup=back)

@bot.on_message(filters.private & StatusFilter(STATUS_PREFIX))
async def add_admin_receive_forward_or_id(client, message):
    user_id = str(message.from_user.id)
    user_pending = pending_get_admin_msgs.get(message.from_user.id)
    if user_pending:
        try:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=user_pending["message_id"]
            )
        except Exception:
            pass  # ignore if already deleted
        del pending_get_admin_msgs[message.from_user.id]
    mer = await message.reply_text("Please Wait...")
    pending_get_admin_msgs[message.from_user.id] = {"message_id": mer.id}
    # --- Load status and extract bot_id ---
    
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
            status = status_data.get(user_id, "")
            if status.startswith(STATUS_PREFIX):
                bot_id = status.replace(STATUS_PREFIX, "")
            else:
                bot_id = None
    except Exception:
        await mer.edit_text("⚠️ Could not read your session. Please try again or restart the process.")
        return

    if not bot_id:
        await mer.edit_text("⚠️ Bot ID not found in your session. Please try again.")
        return

    # --- Try to extract candidate admin id in two ways ---
    candidate_id = None
    reason = None
    back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back" , callback_data=f"manage_admins_{bot_id}")]
    ])

    # 1) Forwarded message from private user
    forwarded_user = getattr(message, "forward_from", None)
    forwarded_chat = getattr(message, "forward_from_chat", None)
    forward_sender_name = getattr(message, "forward_sender_name", None)

    if forwarded_user and forwarded_chat is None and not forward_sender_name:
        # This is a forwarded message from a private user
        candidate_id = int(forwarded_user.id)
        reason = "forward"
    else:
        # 2) Direct numeric user id (optional)
        text = (message.text or "").strip()
        if re.fullmatch(r"\d{5,}", text):   # basic numeric id check (at least 5 digits)
            candidate_id = int(text)
            reason = "direct_id"

    if not candidate_id:
        await mer.edit_text(
            "⚠️ Please either forward a message from the private user you want to add, "
            "or send the user's numeric Telegram ID (digits only).\n\n"
            "Note: group/channel forwards are not accepted."
        )
        return

    # --- Fetch webhook_base_url and bot_token early (needed to call getChat) ---
    webhook_base_url = get_webhook_base_url(bot_id)
    bot_token = get_bot_token_by_id(bot_id)

    if webhook_base_url == "N/A" or bot_token == "N/A":
        await mer.edit_text("⚠️ Unable to fetch bot information. Please try again later.")
        # clear status
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return

    # --- Verify candidate_id is a private user using Telegram getChat ---
    try:
        tg_resp = requests.get(f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={candidate_id}", timeout=10)
        tg_json = tg_resp.json()
        if not tg_json.get("ok"):
            await mer.edit_text("⚠️ Could not verify the provided user ID. Make sure the ID is correct and started the bot.", reply_markup=back)
            # clear status
            status_data[user_id] = ""
            with open(status_user_file, "w") as f:
                json.dump(status_data, f, indent=2)
            return
        chat_info = tg_json.get("result", {})
        chat_type = chat_info.get("type", "")  # should be "private" for a user
        if chat_type != "private":
            await mer.edit_text("⚠️ The specified ID or forwarded message is not from a private user.", reply_markup=back)
            status_data[user_id] = ""
            with open(status_user_file, "w") as f:
                json.dump(status_data, f, indent=2)
            return
        # optional: get full name for confirmation
        first_name = chat_info.get("first_name", "")
        last_name = chat_info.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or f"User {candidate_id}"
    except Exception as e:
        await mer.edit_text(f"⚠️ Failed to verify user with Telegram: `{e}`", reply_markup=back)
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return

    # --- Build ADMINS.json URL and fetch existing admins ---
    admins_url = f"{webhook_base_url}/auth{bot_token}/ADMINS.json"
    try:
        r = requests.get(admins_url, timeout=10)
        admins_resp = r.json()
    except Exception as e:
        await mer.edit_text(f"⚠️ Failed to fetch admin data: `{e}`", reply_markup=back)
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return

    # If ADMINS.json missing -> create base structure using bots.json
    if "error" in admins_resp:
        # load bot meta from bots.json
        try:
            encoded = base64.b64encode(webhook_base_url.encode()).decode()
            bots_json_url = f"https://botdata123.singodiya.tech/{encoded}/bots.json"
            resp = requests.get(bots_json_url, timeout=10)
            bots_data = resp.json()
            bot_entry = bots_data.get(bot_id, {})
            owner_id = bot_entry.get("owner_id")
            is_premium = is_premium_active(bot_id)
            current_admins = []
            owners = [owner_id] if owner_id else []
        except Exception:
            await mer.edit_text("⚠️ Failed to fetch bot metadata. Cannot create ADMINS.json.", reply_markup=back)
            status_data[user_id] = ""
            with open(status_user_file, "w") as f:
                json.dump(status_data, f, indent=2)
            return
    else:
        admin_data = admins_resp.get("data", {})
        owners = admin_data.get("owner", [])
        current_admins = admin_data.get("admin", [])
        # determine premium from bots.json
        try:
            is_premium = is_premium_active(bot_id)
        except Exception:
            is_premium = False

    # --- Permission: only owner or existing admin can add new admin ---
    caller_id = int(message.from_user.id)
    if (caller_id not in owners) and (caller_id not in current_admins):
        await mer.edit_text("⚠️ You are not authorized to add admins for this bot.", reply_markup=back)
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return

    # --- Check duplicates / owner ---
    if candidate_id in owners or candidate_id in current_admins:
        await mer.edit_text("ℹ️ This user is already an owner/admin.", reply_markup=back)
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return

    # --- Admin limit based on premium ---
    max_admins = 5 if is_premium else 2
    if len(current_admins) >= max_admins:
        await mer.edit_text(
            f"⚠️ Admin limit reached. This bot allows up to {max_admins} admin(s). "
            "Upgrade to premium to increase this limit.", reply_markup=back
        )
        status_data[user_id] = ""
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return

    # --- Add new admin and POST ADMINS.json ---
    updated_admins = current_admins + [candidate_id]
    payload = {
        "owner": owners,
        "admin": updated_admins
    }

    try:
        post_resp = requests.post(admins_url, json=payload, timeout=10)
        if post_resp.status_code in (200, 201):
            await mer.edit_text(f"✅ Successfully added **{full_name}** (`{candidate_id}`) as admin.", reply_markup=back)
        else:
            await mer.edit_text(
                f"❌ Failed to update admins. Server responded with status {post_resp.status_code}."
            , reply_markup=back)
    except Exception as e:
        await mer.edit_text(f"❌ Failed to send update request: `{e}`", reply_markup=back)

    # --- Clear user status ---
    status_data[user_id] = ""
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import json
import base64
import requests
from onlyfunctions import get_webhook_base_url, get_bot_token_by_id
from common_data import status_user_file

@bot.on_callback_query(filters.regex(r"^remove_admin_(\d+)$"))
async def remove_admin_cb(client, query):
    bot_id = query.data.split("_")[-1]
    user_id = str(query.from_user.id)
    back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back" , callback_data=f"manage_admins_{bot_id}")]
    ])

    await query.message.edit_text("⏳ Loading admin list, please wait...",reply_markup=back)

    # --- Fetch bot info ---
    webhook_base_url = get_webhook_base_url(bot_id)
    bot_token = get_bot_token_by_id(bot_id)
    if webhook_base_url == "N/A" or bot_token == "N/A":
        await query.message.edit_text("⚠️ Unable to fetch bot information.")
        return

    # --- Get ADMINS.json ---
    admins_url = f"{webhook_base_url}/auth{bot_token}/ADMINS.json"
    try:
        r = requests.get(admins_url, timeout=10)
        resp = r.json()
        if "error" in resp:
            await query.message.edit_text("ℹ️ No admins found for this bot yet.",reply_markup=back)
            return
        owners = resp.get("data", {}).get("owner", [])
        current_admins = resp.get("data", {}).get("admin", [])
    except Exception as e:
        await query.message.edit_text(f"⚠️ Failed to fetch admin data: `{e}`",reply_markup=back)
        return

    # --- Skip owner in list ---
    removable_admins = [a for a in current_admins if a not in owners]

    if not removable_admins:
        await query.message.edit_text("ℹ️ No admins available to remove.", reply_markup=back)
        return

    # --- Build buttons ---
    buttons = []
    for aid in removable_admins:
        buttons.append([InlineKeyboardButton(f"{aid}", callback_data=f"confirm_remove_{bot_id}_{aid}")])
    buttons.append([InlineKeyboardButton("⬅️ Cancel", callback_data=f"manage_admins_{bot_id}")])

    await query.message.edit_text(
        f"🗑️ Select an admin to remove for Bot ID `{bot_id}`:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- Confirmation callback ---
@bot.on_callback_query(filters.regex(r"^confirm_remove_(\d+)_(\d+)$"))
async def confirm_remove_admin_cb(client, query):
    bot_id, admin_id = query.matches[0].groups()
    admin_id = int(admin_id)

    # Confirmation buttons
    buttons = [
        [
            InlineKeyboardButton("✅ Yes, remove", callback_data=f"do_remove_admin_{bot_id}_{admin_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"remove_admin_{bot_id}")
        ]
    ]
    await query.message.edit_text(
        f"⚠️ Are you sure you want to remove admin `{admin_id}` from Bot `{bot_id}`?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- Execute removal ---
@bot.on_callback_query(filters.regex(r"^do_remove_admin_(\d+)_(\d+)$"))
async def do_remove_admin_cb(client, query):
    bot_id, admin_id = query.matches[0].groups()
    admin_id = int(admin_id)

    webhook_base_url = get_webhook_base_url(bot_id)
    bot_token = get_bot_token_by_id(bot_id)
    admins_url = f"{webhook_base_url}/auth{bot_token}/ADMINS.json"

    try:
        r = requests.get(admins_url, timeout=10)
        resp = r.json()
        owners = resp.get("data", {}).get("owner", [])
        current_admins = resp.get("data", {}).get("admin", [])
    except Exception as e:
        await query.message.edit_text(f"⚠️ Failed to fetch admin data: `{e}`")
        return

    if admin_id not in current_admins:
        await query.message.edit_text(f"ℹ️ Admin `{admin_id}` is no longer in the list.")
        return

    # Remove admin
    updated_admins = [a for a in current_admins if a != admin_id]
    payload = {
        "owner": owners,
        "admin": updated_admins
    }

    try:
        post_resp = requests.post(admins_url, json=payload, timeout=10)
        if post_resp.status_code in (200, 201):
            back = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back" , callback_data=f"manage_admins_{bot_id}")]
    ])
            await query.message.edit_text(f"✅ Successfully removed admin `{admin_id}`.",reply_markup=back)
        else:
            await query.message.edit_text(f"❌ Failed to remove admin. Status: {post_resp.status_code}")
    except Exception as e:
        await query.message.edit_text(f"❌ Failed to remove admin: `{e}`")