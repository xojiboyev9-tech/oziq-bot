Oziq-ovqat do'koni uchun Telegram bot (Mini App)
Bu loyiha to'liq telefondan (kompyutersiz) joylab ishga tushirish uchun tayyorlangan.
Botning imkoniyatlari
🛒 Telegram ichida ochiladigan mini-ilova (katalog + savat)
📦 Buyurtma qabul qilish, adminlarga darhol xabar borishi
✅ Admin "Qabul qilish" → "Tayyor" bosgach, mijozga avtomatik xabar boradi
📜 Mijoz uchun "Mening buyurtmalarim"
⚙️ Admin panel: mahsulot qo'shish, mahsulotlar/buyurtmalar ro'yxati
📢 Barcha foydalanuvchilarga umumiy xabar yuborish
1-qadam: Bot yaratish
Telegramda @BotFather ga o'ting, /newbot yozing.
Bot nomi va username so'raladi (username bot bilan tugashi kerak, masalan OziqDokonBot).
Sizga token beriladi (masalan 123456:AAExxxxx). Uni saqlab qo'ying — hech kimga bermang.
2-qadam: O'z Telegram ID'ingizni bilib olish
@userinfobot ga /start yozing — u sizga ID raqamingizni beradi (masalan 123456789).
Shu raqam — siz admin bo'lasiz.
3-qadam: Kodni GitHub'ga joylash (telefon brauzeridan)
github.com'da hisob oching (agar yo'q bo'lsa).
Brauzeringizni "Desktop site" rejimiga o'tkazish tavsiya etiladi (tugmalar qulayroq chiqadi).
Yangi repository yarating: New repository → nom bering (masalan oziq-bot) → Create repository.
Har bir fayl uchun: Add file → Create new file, fayl nomini yozing (masalan bot.py), ichiga shu loyihadagi faylning tarkibini nusxalab qo'ying, pastda Commit changes.
Quyidagi barcha fayllarni shu tarzda qo'shing: bot.py, database.py, config.py, requirements.txt, Procfile, va webapp/index.html, webapp/style.css, webapp/app.js (papka nomini fayl nomi oldiga yozsangiz, masalan webapp/index.html, GitHub o'zi papka yaratadi).
Maslahat: agar sizga qulayroq bo'lsa, shu suhbatdagi tayyor zip faylni yuklab olib, uni GitHub'ning "Upload files" (drag & drop) bo'limiga yuklashingiz ham mumkin — bu birma-bir fayl yaratishdan tezroq.
4-qadam: Railway'da joylash (deploy)
railway.app saytiga o'ting, GitHub hisobingiz orqali kiring.
New Project → Deploy from GitHub repo → yaratgan oziq-bot repongizni tanlang.
Railway avtomatik Python loyihasini aniqlaydi va o'rnatadi.
Variables (Environment Variables) bo'limiga o'ting va quyidagilarni qo'shing:
BOT_TOKEN = BotFather'dan olgan tokeningiz
ADMIN_IDS = sizning Telegram ID'ingiz (bir nechta bo'lsa vergul bilan: 12345,67890)
WEBAPP_URL = hozircha bo'sh qoldiring, keyingi qadamda to'ldiramiz
Settings bo'limida Networking → Generate Domain tugmasini bosing — sizga masalan oziq-bot-production.up.railway.app kabi manzil beradi.
Shu manzilni oling va WEBAPP_URL qiymatini quyidagicha yangilang: https://oziq-bot-production.up.railway.app/webapp/ (oxirida /webapp/ bo'lishi shart)
Loyiha qayta deploy bo'ladi (Railway buni avtomatik qiladi environment o'zgarganda).
5-qadam: Botni tekshirish
Telegramda botingizga o'ting, /start bosing.
"🛒 Do'kon" tugmasini bosing — mini-ilova ochilib, namunaviy mahsulotlar (Non, Sut, Tuxum, Olma) ko'rinishi kerak.
Mahsulot tanlab, "Buyurtma berish" tugmasini bosing.
Admin (siz) darhol yangi buyurtma haqida xabar olasiz, "✅ Qabul qilish" / "❌ Bekor qilish" tugmalari bilan.
Qabul qilgach, "🍳 Tayyor deb belgilash" tugmasi chiqadi — bosgach mijozga avtomatik "buyurtmangiz tayyor" xabari boradi.
Mahsulot qo'shish / boshqarish
Botda ⚙️ Admin panel tugmasi orqali:
➕ Mahsulot qo'shish — nomi, narxi, kategoriyasi, tavsifini ketma-ket so'raydi
📋 Mahsulotlar ro'yxati — barcha mahsulotlar va holatini ko'rsatadi
📊 Buyurtmalar — so'nggi buyurtmalar ro'yxati
📢 Xabar yuborish — barcha mijozlarga bir xabar yuborish
Keyinroq qo'shsa bo'ladigan funksiyalar
Mahsulot rasmlarini yuklash
Click/Payme orqali onlayn to'lov
Yetkazib berish manzili so'rash
Mahsulotni admin panelidan tahrirlash/o'chirish tugmalari
Savol yoki qo'shimcha funksiya kerak bo'lsa — shu suhbatda so'rashingiz mumkin.
