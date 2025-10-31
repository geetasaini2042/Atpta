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

import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@bot.on_callback_query(filters.regex(r"^premium_(\d+)$"))
async def premium_plans(client, query):
    bot_id = query.data.split("_")[-1]
    await query.message.edit_text("⏳ Please Wait...")
    try:
        # 🔹 plans.json से डेटा प्राप्त करें
        response = requests.get("https://botdata123.singodiya.tech/plans.json")
        data = response.json()
        plans = data.get("plans", {})
        premium_features = data.get("premium_features", [])

        # 🔹 सभी plans को एक सुंदर टेक्स्ट में बदलें
        text = "💎 **Premium Plans Available:**\n\n"
        for key, plan in plans.items():
            text += f"**{plan['name']}**\n"
            text += f"🕒 Duration: {plan['duration_days']} days\n"
            text += f"💰 Price: ₹{plan['price']}\n"
            if 'discount' in plan:
                text += f"🎁 Discount: {plan['discount']}\n"
            text += f"📜 {plan['description']}\n\n"

        # 🔹 Premium features लिस्ट जोड़ें
        if premium_features:
            text += "✨ **Premium Features:**\n"
            for feat in premium_features:
                text += f"• {feat}\n"

        # 🔹 Inline बटन
        buttons = InlineKeyboardMarkup(
            [
              [
                InlineKeyboardButton("🚀 Upgrade Now", url="https://t.me/mr_singodiyabot")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data=f"bot_details_{bot_id}")]
            ]
        )

        # 🔹 मेसेज अपडेट करें
        await query.message.edit_text(
            text,
            reply_markup=buttons,
            disable_web_page_preview=True
        )

    except Exception as e:
        await query.message.edit_text(f"⚠️ Error loading plans:\n`{e}`")