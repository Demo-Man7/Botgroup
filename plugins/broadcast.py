import json
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID

DATA_FILE = "users.json"


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"users": [], "chats": []}
    return {"users": [], "chats": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Private Chat ထဲမှာ /start နှိပ်သူများ (User ID) သိမ်းခြင်း
@Client.on_message(filters.command("start") & filters.private, group=10)
async def save_user(client: Client, message: Message):
    data = load_data()
    user_id = message.from_user.id
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)


# ⭐ [အဓိက အပြောင်းအလဲ] Bot ကို Group ထဲ ရှိနေသမျှ (သို့) ထည့်လိုက်သည်နှင့် ချက်ချင်း Group ID သိမ်းပေးမည့် Event
@Client.on_my_chat_member_updated(group=10)
async def auto_save_chat(client: Client, chat_member):
    # Bot ကို Group ထဲ ထည့်လိုက်ချိန် (သို့) Bot က Group ထဲမှာ ရှိနေဆဲဖြစ်ကြောင်း သိရှိချိန်
    if chat_member.new_chat_member and chat_member.new_chat_member.status in ["member", "administrator"]:
        data = load_data()
        chat_id = chat_member.chat.id
        if chat_id not in data["chats"]:
            data["chats"].append(chat_id)
            save_data(data)


# Broadcast ပြုလုပ်သည့် Command
@Client.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_message(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "ကျေးဇူးပြု၍ Broadcast လုပ်လိုသည့် စာသား (သို့) ပုံကို Reply လုပ်ပြီးမှ /broadcast ဟု ပို့ပါ။"
        )
    
    data = load_data()
    users = data.get("users", [])
    chats = data.get("chats", [])
    
    query = message.reply_to_message
    success_users = 0
    success_chats = 0
    
    # User များသို့ ပို့ခြင်း
    for uid in users:
        try:
            await query.copy(chat_id=uid)
            success_users += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
            
    # Group များကို ပို့ခြင်း
    for cid in chats:
        try:
            await query.copy(chat_id=cid)
            success_chats += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass
            
    total = success_users + success_chats
    await message.reply_text(
        f"✅ **Broadcast ပြီးစီးပါပြီ**\n\n"
        f"👤 User ဆီသို့ ရောက်ရှိမှု: {success_users} ဦး\n"
        f"👥 Group ဆီသို့ ရောက်ရှိမှု: {success_chats} ခု\n"
        f"📊 စုစုပေါင်း ပို့ပြီးစီးမှု: {total} ခု"
    )
