import json
import os
import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.errors import FloodWait
from config import OWNER_ID

logger = logging.getLogger(__name__)

DATA_FILE = "users.json"
_broadcast_lock = asyncio.Lock()  # တစ်ချိန်တည်း broadcast ၂ ခု မဖြစ်စေရန်


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


@Client.on_message(filters.command("start") & filters.private, group=10)
async def save_user(client: Client, message: Message):
    data = await asyncio.to_thread(load_data)
    user_id = message.from_user.id
    if user_id not in data["users"]:
        data["users"].append(user_id)
        await asyncio.to_thread(save_data, data)


@Client.on_chat_member_updated(group=10)
async def auto_save_chat(client: Client, chat_member: ChatMemberUpdated):
    new_m = getattr(chat_member, "new_chat_member", None) or getattr(chat_member, "new_member", None)
    if new_m and new_m.user.id == client.me.id:
        if new_m.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]:
            data = await asyncio.to_thread(load_data)
            chat_id = chat_member.chat.id
            if chat_id not in data["chats"]:
                data["chats"].append(chat_id)
                await asyncio.to_thread(save_data, data)


# FloodWait ကို ကိုင်တွယ်ပြီး ပို့ပေးမည့် helper
async def _safe_send(query: Message, chat_id: int, retries: int = 3):
    for attempt in range(retries):
        try:
            await query.copy(chat_id=chat_id)
            return True, None
        except FloodWait as e:
            wait = e.value + 3
            logger.warning(f"FloodWait {wait}s → chat {chat_id}")
            await asyncio.sleep(wait)
        except Exception as e:
            return False, str(e)
    return False, "Max retries exceeded"


@Client.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_message(client: Client, message: Message):
    if _broadcast_lock.locked():
        return await message.reply_text(
            "⚠️ Broadcast တစ်ခု လုပ်ဆောင်နေဆဲဖြစ်ပါတယ်။ ပြီးဆုံးသည်အထိ စောင့်ပါ။"
        )

    if not message.reply_to_message:
        return await message.reply_text(
            "ကျေးဇူးပြု၍ Broadcast လုပ်လိုသည့် စာသား (သို့) ပုံကို Reply လုပ်ပြီးမှ /broadcast ဟု ပို့ပါ။"
        )

    async with _broadcast_lock:
        data   = await asyncio.to_thread(load_data)
        users  = data.get("users", [])
        chats  = data.get("chats", [])
        query  = message.reply_to_message

        status = await message.reply_text("📤 Broadcast စတင်နေပါပြီ...")

        ok_users = ok_chats = fail_users = fail_chats = 0

        # User များ
        for uid in users:
            ok, err = await _safe_send(query, uid)
            if ok:
                ok_users += 1
            else:
                fail_users += 1
                logger.warning(f"User {uid} failed: {err}")
            await asyncio.sleep(0.5)   # ⭐ ၀.၅ စက္ကန့် ခြား

        # Group များ
        for cid in chats:
            ok, err = await _safe_send(query, cid)
            if ok:
                ok_chats += 1
            else:
                fail_chats += 1
                logger.warning(f"Chat {cid} failed: {err}")
            await asyncio.sleep(0.5)

        await status.edit_text(
            f"✅ **Broadcast ပြီးစီးပါပြီ**\n\n"
            f"👤 User ရောက်ရှိမှု: {ok_users} ဦး (မအောင်: {fail_users})\n"
            f"👥 Group ရောက်ရှိမှု: {ok_chats} ခု (မအောင်: {fail_chats})\n"
            f"📊 စုစုပေါင်း: {ok_users + ok_chats} ခု\n"
            f"❌ မအောင်မြင်မှု: {fail_users + fail_chats} ခု"
        )
