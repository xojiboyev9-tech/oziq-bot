import asyncio
import json
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppData,
)

import config
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

PHOTOS_DIR = "webapp/photos"

# Mahsulot qo'shilganda miqdor so'ralmaydi - shu standart miqdor bilan
# "sotuvda" deb belgilanadi. Keyinchalik "🗃 Ombor" orqali aniqlashtirish mumkin.
DEFAULT_QUANTITY = 100


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ---------------- FSM holatlari ----------------

class AddProduct(StatesGroup):
    name = State()
    price = State()
    category = State()
    description = State()
    photo = State()


class Broadcast(StatesGroup):
    text = State()


class StockManage(StatesGroup):
    waiting = State()


# ---------------- Klaviaturalar ----------------

def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🛒 Do'kon", web_app=WebAppInfo(url=config.WEBAPP_URL))],
        [KeyboardButton(text="📦 Mening buyurtmalarim")],
    ]
    if is_admin(user_id):
        rows.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def phone_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
    )


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="🗃 Ombor")],
            [KeyboardButton(text="📊 Buyurtmalar"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True,
    )


def order_admin_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"acc:{order_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"rej:{order_id}"),
        ]
    ])


def order_ready_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍳 Tayyor deb belgilash", callback_data=f"rdy:{order_id}")]
    ])


# ---------------- Foydalanuvchi buyruqlari ----------------

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = db.get_user(message.from_user.id)
    db.upsert_user(message.from_user.id, message.from_user.full_name, message.from_user.username)

    # Agar foydalanuvchi birinchi marta kirsa yoki telefon raqami saqlanmagan bo'lsa,
    # avval raqamni so'raymiz.
    if not user or not user.get("phone"):
        await message.answer(
            "Assalomu alaykum! 🛒 Oziq-ovqat do'koniga xush kelibsiz.\n\n"
            "Botdan foydalanishdan oldin, iltimos, telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_kb(),
        )
        return

    await message.answer(
        "Assalomu alaykum! 🛒 Oziq-ovqat do'koniga xush kelibsiz.\n\n"
        "Pastdagi \"🛒 Do'kon\" tugmasi orqali mahsulotlarni ko'rib, buyurtma bera olasiz.",
        reply_markup=main_menu_kb(message.from_user.id),
    )


@router.message(F.contact)
async def contact_received(message: Message):
    contact = message.contact

    # Boshqa birovning kontaktini forward qilib yuborishining oldini olamiz
    if contact.user_id != message.from_user.id:
        await message.answer(
            "Iltimos, \"📱 Raqamni yuborish\" tugmasi orqali faqat o'zingizning "
            "raqamingizni yuboring."
        )
        return

    db.upsert_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username,
        phone=contact.phone_number,
    )
    await message.answer(
        "✅ Rahmat! Endi botdan to'liq foydalanishingiz mumkin.\n\n"
        "Pastdagi \"🛒 Do'kon\" tugmasi orqali mahsulotlarni ko'rib, buyurtma bera olasiz.",
        reply_markup=main_menu_kb(message.from_user.id),
    )


@router.message(F.text == "📦 Mening buyurtmalarim")
async def my_orders(message: Message):
    orders = db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer("Sizda hali buyurtmalar yo'q.")
        return

    status_names = {
        "yangi": "🆕 Yangi",
        "qabul qilindi": "👨‍🍳 Qabul qilindi, tayyorlanmoqda",
        "tayyor": "✅ Tayyor",
        "bekor qilindi": "❌ Bekor qilindi",
    }
    lines = []
    for o in orders:
        items_text = ", ".join(f"{it['name']} x{it['qty']}" for it in o["items"])
        lines.append(
            f"Buyurtma #{o['id']} — {status_names.get(o['status'], o['status'])}\n"
            f"{items_text}\nJami: {o['total']} so'm\n"
        )
    await message.answer("\n".join(lines))


@router.message(F.web_app_data)
async def handle_webapp_order(message: Message):
    # Telefon raqami bo'lmagan foydalanuvchi to'g'ridan-to'g'ri buyurtma bermasin
    user = db.get_user(message.from_user.id)
    if not user or not user.get("phone"):
        await message.answer(
            "Buyurtma berishdan oldin telefon raqamingizni yuboring 👇",
            reply_markup=phone_request_kb(),
        )
        return

    try:
        data = json.loads(message.web_app_data.data)
        items = data["items"]  # [{id, name, price, qty}]
        total = data["total"]
    except Exception:
        await message.answer("Buyurtmada xatolik yuz berdi, qaytadan urinib ko'ring.")
        return

    if not items:
        await message.answer("Savat bo'sh edi.")
        return

    order_id = db.create_order(message.from_user.id, items, total)
    db.upsert_user(message.from_user.id, message.from_user.full_name, message.from_user.username)

    await message.answer(
        f"✅ Buyurtmangiz qabul qilindi! Raqami: #{order_id}\n"
        f"Jami: {total} so'm\n\nTez orada tasdiqlanadi.",
        reply_markup=main_menu_kb(message.from_user.id),
    )

    items_text = "\n".join(f"• {it['name']} x{it['qty']} — {it['price']*it['qty']} so'm" for it in items)
    phone_line = f"📱 Tel: {user['phone']}\n" if user.get("phone") else ""
    admin_text = (
        f"🆕 Yangi buyurtma #{order_id}\n"
        f"Mijoz: {message.from_user.full_name} (@{message.from_user.username or '—'})\n"
        f"{phone_line}\n"
        f"{items_text}\n\nJami: {total} so'm"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=order_admin_kb(order_id))
        except Exception as e:
            logger.warning(f"Adminga xabar yuborilmadi ({admin_id}): {e}")


# ---------------- Admin: buyurtma holatini boshqarish ----------------

@router.callback_query(F.data.startswith("acc:"))
async def order_accept(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    db.update_order_status(order_id, "qabul qilindi")
    order = db.get_order(order_id)
    await callback.message.edit_text(
        callback.message.text + "\n\n👨‍🍳 Qabul qilindi, tayyorlanmoqda",
        reply_markup=order_ready_kb(order_id),
    )
    try:
        await bot.send_message(
            order["user_id"],
            f"👨‍🍳 Buyurtmangiz #{order_id} qabul qilindi va tayyorlanmoqda!",
        )
    except Exception as e:
        logger.warning(f"Mijozga xabar yuborilmadi: {e}")
    await callback.answer("Qabul qilindi")


@router.callback_query(F.data.startswith("rej:"))
async def order_reject(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    db.update_order_status(order_id, "bekor qilindi")
    order = db.get_order(order_id)
    await callback.message.edit_text(callback.message.text + "\n\n❌ Bekor qilindi")
    try:
        await bot.send_message(
            order["user_id"],
            f"❌ Afsuski, buyurtmangiz #{order_id} bekor qilindi. Savol uchun do'konga murojaat qiling.",
        )
    except Exception as e:
        logger.warning(f"Mijozga xabar yuborilmadi: {e}")
    await callback.answer("Bekor qilindi")


@router.callback_query(F.data.startswith("rdy:"))
async def order_ready(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    db.update_order_status(order_id, "tayyor")
    order = db.get_order(order_id)
    await callback.message.edit_text(callback.message.text + "\n\n✅ Tayyor")
    try:
        await bot.send_message(
            order["user_id"],
            f"✅ Xursandchilik bilan xabar beramiz — buyurtmangiz #{order_id} tayyor bo'ldi! "
            f"Iltimos, do'kondan olib keting.",
        )
    except Exception as e:
        logger.warning(f"Mijozga xabar yuborilmadi: {e}")
    await callback.answer("Mijozga xabar yuborildi")


# ---------------- Admin panel ----------------

@router.message(F.text == "⚙️ Admin panel")
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Admin panel:", reply_markup=admin_menu_kb())


@router.message(F.text == "⬅️ Orqaga")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bosh menyu:", reply_markup=main_menu_kb(message.from_user.id))


@router.message(F.text.lower().in_({"bekor", "/cancel", "bekor qilish"}))
async def cancel_any_flow(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        return  # hech qanday jarayonda emas, boshqa handlerlarga berilsin
    await state.clear()
    if is_admin(message.from_user.id):
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_kb())
    else:
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb(message.from_user.id))


# ---------------- Mahsulot qo'shish (nom -> narx -> kategoriya -> tavsif -> rasm) ----------------
# Eslatma: miqdor endi bu yerda so'ralmaydi - yangi mahsulot avtomatik
# DEFAULT_QUANTITY bilan qo'shiladi. Aniq miqdorni "🗃 Ombor" orqali kiritish mumkin.

@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddProduct.name)
    await message.answer(
        "Mahsulot nomini kiriting:\n\n"
        "(Istalgan vaqtda bekor qilish uchun \"bekor\" deb yozing)"
    )


@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Narxini kiriting (faqat son, so'mda):")


@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting. Masalan: 15000")
        return
    await state.update_data(price=int(message.text))
    await state.set_state(AddProduct.category)
    await message.answer("Kategoriyasini kiriting (masalan: Meva-sabzavot):")


@router.message(AddProduct.category)
async def add_product_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(AddProduct.description)
    await message.answer("Qisqacha tavsif kiriting (yoki - yozing, agar kerak bo'lmasa):")


@router.message(AddProduct.description)
async def add_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text if message.text != "-" else "")
    await state.set_state(AddProduct.photo)
    await message.answer(
        "Endi mahsulot rasmini yuboring 📷 (galereyadan tanlang yoki suratga oling).\n"
        "Agar rasm qo'ymoqchi bo'lmasangiz, \"-\" deb yozing."
    )


@router.message(AddProduct.photo, F.photo)
async def add_product_photo_received(message: Message, state: FSMContext):
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    photo = message.photo[-1]  # eng yuqori sifatdagi versiyasi
    file = await bot.get_file(photo.file_id)
    filename = f"{photo.file_unique_id}.jpg"
    local_path = os.path.join(PHOTOS_DIR, filename)
    await bot.download_file(file.file_path, local_path)
    photo_url = f"/webapp/photos/{filename}"

    await _finish_add_product(message, state, photo_url)


@router.message(AddProduct.photo, F.text == "-")
async def add_product_photo_skipped(message: Message, state: FSMContext):
    await _finish_add_product(message, state, photo_url="")


@router.message(AddProduct.photo)
async def add_product_photo_invalid(message: Message):
    await message.answer("Iltimos, rasm yuboring 📷 yoki o'tkazib yuborish uchun \"-\" deb yozing.")


async def _finish_add_product(message: Message, state: FSMContext, photo_url: str):
    data = await state.get_data()
    db.add_product(
        name=data["name"],
        price=data["price"],
        quantity=DEFAULT_QUANTITY,
        description=data["description"],
        category=data["category"],
        photo_url=photo_url,
    )
    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi: {data['name']} — {data['price']} so'm\n"
        f"📦 Miqdor: {DEFAULT_QUANTITY} dona (standart) — kerak bo'lsa \"🗃 Ombor\" orqali o'zgartiring"
        + (" (rasm bilan)" if photo_url else ""),
        reply_markup=admin_menu_kb(),
    )


# ---------------- Ombor: miqdorni ko'rish / o'zgartirish / mahsulotni o'chirish ----------------

@router.message(F.text == "🗃 Ombor")
async def stock_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    products = db.get_products(in_stock_only=False)
    if not products:
        await message.answer("Katalog bo'sh.")
        return

    lines = [
        f"#{p['id']} {p['name']} — {p['price']} so'm — {p.get('quantity', 0)} dona "
        f"({'✅ sotuvda' if p['in_stock'] else '⛔️ tugagan'})"
        for p in products
    ]
    text = (
        "📦 Ombordagi mahsulotlar:\n\n" + "\n".join(lines) +
        "\n\nMiqdorni belgilash: ID MIQDOR (masalan: 3 15 — 15 ga tenglashtiradi)\n"
        "Qo'shish: ID +MIQDOR (masalan: 3 +5 — 5 dona qo'shadi)\n"
        "Ayirish: ID -MIQDOR (masalan: 3 -5 — 5 dona ayiradi)\n"
        "Mahsulotni o'chirish: shunchaki ID raqamini yozing (masalan: 3)\n"
        "Chiqish uchun \"bekor\" deb yozing yoki ⬅️ Orqaga tugmasini bosing."
    )
    await state.set_state(StockManage.waiting)
    await message.answer(text)


@router.message(StockManage.waiting)
async def stock_manage_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    parts = message.text.strip().split()

    # Yagona narsa - ID raqami: mahsulotni o'chirish (masalan: "3")
    if len(parts) == 1 and parts[0].isdigit():
        pid = int(parts[0])
        product = db.get_product(pid)
        if not product:
            await message.answer(f"#{pid} raqamli mahsulot topilmadi.")
            return
        db.delete_product(pid)
        await message.answer(f"🗑 #{pid} {product['name']} o'chirildi.")
        return

    # Eski uslub bilan moslik uchun: "ochir 3"
    if len(parts) == 2 and parts[0].lower() in ("ochir", "o'chir", "oʻchir"):
        if not parts[1].isdigit():
            await message.answer("Noto'g'ri format. Masalan: 3 (yoki ochir 3)")
            return
        pid = int(parts[1])
        product = db.get_product(pid)
        if not product:
            await message.answer(f"#{pid} raqamli mahsulot topilmadi.")
            return
        db.delete_product(pid)
        await message.answer(f"🗑 #{pid} {product['name']} o'chirildi.")
        return

    # Miqdorni o'zgartirish: "3 15" (yangisini belgilash) yoki "3 +5" / "3 -5" (qo'shish/ayirish)
    if len(parts) == 2 and parts[0].isdigit():
        pid = int(parts[0])
        amount_str = parts[1]
        product = db.get_product(pid)
        if not product:
            await message.answer(f"#{pid} raqamli mahsulot topilmadi.")
            return

        if amount_str.startswith(("+", "-")) and amount_str[1:].isdigit():
            delta = int(amount_str)
            new_qty = max(0, product.get("quantity", 0) + delta)
            db.set_product_quantity(pid, new_qty)
            status = "✅ sotuvda" if new_qty > 0 else "⛔️ tugagan"
            sign = "qo'shildi" if delta > 0 else "ayirildi"
            await message.answer(
                f"📦 #{pid} {product['name']} — {abs(delta)} dona {sign}, "
                f"yangi miqdor: {new_qty} dona ({status})"
            )
            return
        elif amount_str.isdigit():
            qty = int(amount_str)
            db.set_product_quantity(pid, qty)
            status = "✅ sotuvda" if qty > 0 else "⛔️ tugagan"
            await message.answer(f"📦 #{pid} {product['name']} — yangi miqdor: {qty} dona ({status})")
            return

    await message.answer(
        "Noto'g'ri format.\n"
        "O'chirish: shunchaki ID raqamini yozing (masalan: 3)\n"
        "Miqdorni o'zgartirish: ID MIQDOR (masalan: 3 15)"
    )


@router.message(F.text == "📊 Buyurtmalar")
async def list_orders(message: Message):
    if not is_admin(message.from_user.id):
        return
    orders = db.get_all_orders()
    if not orders:
        await message.answer("Hali buyurtmalar yo'q.")
        return
    lines = [f"#{o['id']} — {o['status']} — {o['total']} so'm" for o in orders]
    await message.answer("\n".join(lines))


@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.text)
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:")


@router.message(Broadcast.text)
async def broadcast_send(message: Message, state: FSMContext):
    await state.clear()
    user_ids = db.get_all_user_ids()
    sent = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, f"📢 {message.text}")
            sent += 1
        except Exception:
            pass
        # Telegram flood-limitiga tushmaslik uchun har bir xabar orasida kichik pauza
        await asyncio.sleep(0.05)
    await message.answer(f"Xabar {sent} ta foydalanuvchiga yuborildi.", reply_markup=admin_menu_kb())


# ---------------- Mini App uchun oddiy API ----------------

async def api_products(request: web.Request):
    products = db.get_products(in_stock_only=True)
    response = web.json_response(products)
    # Mini App eski (o'chirilgan/tugagan) mahsulotni ko'rsatib qolmasligi uchun
    # brauzer/Telegram bu javobni keshlab qo'ymasin.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


async def health(request: web.Request):
    return web.Response(text="OK")


async def webapp_index(request: web.Request):
    return web.FileResponse("webapp/index.html")


async def on_startup(app: web.Application):
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    db.init_db()
    db.seed_sample_products()
    asyncio.create_task(dp.start_polling(bot))


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/api/products", api_products)
    app.router.add_get("/health", health)
    app.router.add_get("/webapp/", webapp_index)
    app.router.add_get("/webapp/index.html", webapp_index)
