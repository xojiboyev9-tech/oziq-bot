import os

# BotFather'dan olingan tokenni shu yerga yozing (yoki Railway/Render'da
# Environment Variables bo'limiga BOT_TOKEN nomi bilan qo'shing)
BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ_BU_YERGA")

# Admin(lar)ning Telegram ID raqami(lari). Bir nechta bo'lsa vergul bilan ajrating.
# Telegram ID'ingizni bilish uchun @userinfobot ga /start yozing.
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip()
]

# Mini App (webapp) joylashgan HTTPS manzil. Loyihani deploy qilgach,
# masalan https://sizning-bot.up.railway.app kabi bo'ladi.
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://example.com/webapp/")

# Server porti (Railway/Render o'zi PORT ni beradi, o'zgartirish shart emas)
PORT = int(os.getenv("PORT", "8080"))

DB_PATH = os.getenv("DB_PATH", "shop.db")
