import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# ⭐ Logging ဖွင့်ထားခြင်း (error တွေကို မြင်နိုင်ရန်)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)  # Pyrogram log ကို လျှော့ခြင်း

app = Client(
    "WelcomeBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),

    # ⭐ Connection ပြဿနာ ဖြေရှင်းရန် အဓိက parameter များ
    sleep_threshold=60,   # FloodWait ကို Pyrogram ကိုယ်တိုင် ကိုင်တွယ် (စက္ကန့် ၆၀ အထိ)
    workers=16,           # Dispatcher workers တိုးခြင်း (default 4)
    in_memory=False,      # Session ကို disk မှာ သိမ်း (ပြန် restart ရင် ပြန် login မလိုအပ်)
)

if __name__ == "__main__":
    print("Bot Starting...")
    app.run()
