import asyncio
import json
import logging

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


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ---------------- FSM holatlari ----------------

class AddProduct(StatesGroup):
    name = State()
    price = State()
    description = State()
    category = State()


class Broadcast(StatesGroup):
    text = State()


# ---------------- Klaviaturalar ----------------

def main_menu_kb(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🛒 Do'kon", web_app=WebAppInfo(url=config.WEBAPP_URL))],
        [KeyboardButton(text="📦 Mening buyurtmalarim")],
    ]
    if is_admin(user_id):
        rows.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Mahsulot qo'shish"), KeyboardButton(text="📋 Mahsulotlar ro'yxati")],
            [KeyboardButton(text="📢 Xabar yuborish"), KeyboardButton(text="📊 Buyurtmalar")],
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
    db.upsert_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(
        "Assalomu alaykum! 🛒 Oziq-ovqat do'koniga xush kelibsiz.\n\n"
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
    admin_text = (
        f"🆕 Yangi buyurtma #{order_id}\n"
        f"Mijoz: {message.from_user.full_name} (@{message.from_user.username or '—'})\n\n"
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
async def back_to_main(message: Message):
    await message.answer("Bosh menyu:", reply_markup=main_menu_kb(message.from_user.id))


@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddProduct.name)
    await message.answer("Mahsulot nomini kiriting:")


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
    data = await state.update_data(description=message.text if message.text != "-" else "")
    db.add_product(
        name=data["name"],
        price=data["price"],
        description=data["description"],
        category=data["category"],
    )
    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi: {data['name']} — {data['price']} so'm",
        reply_markup=admin_menu_kb(),
    )


@router.message(F.text == "📋 Mahsulotlar ro'yxati")
async def list_products(message: Message):
    if not is_admin(message.from_user.id):
        return
    products = db.get_products(in_stock_only=False)
    if not products:
        await message.answer("Katalog bo'sh.")
        return
    lines = [f"#{p['id']} {p['name']} — {p['price']} so'm "
             f"({'✅ sotuvda' if p['in_stock'] else '⛔️ tugagan'})" for p in products]
    await message.answer("\n".join(lines))


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
    await message.answer(f"Xabar {sent} ta foydalanuvchiga yuborildi.", reply_markup=admin_menu_kb())


# ---------------- Mini App uchun oddiy API ----------------

async def api_products(request: web.Request):
    products = db.get_products(in_stock_only=True)
    return web.json_response(products)


async def health(request: web.Request):
    return web.Response(text="OK")


async def webapp_index(request: web.Request):
    return web.FileResponse("webapp/index.html")


async def on_startup(app: web.Application):
    db.init_db()
    db.seed_sample_products()
    asyncio.create_task(dp.start_polling(bot))


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/api/products", api_products)
    app.router.add_get("/health", health)
    app.router.add_get("/webapp/", webapp_index)
    app.router.add_get("/webapp/index.html", webapp_index)
    app.router.add_static("/webapp/", path="webapp", name="webapp", show_index=False)
    app.on_startup.append(on_startup)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=config.PORT) 
