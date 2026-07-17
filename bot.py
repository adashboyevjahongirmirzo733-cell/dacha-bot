import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db

# ---------- Sozlamalar (Railway -> Variables orqali beriladi) ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8917124993:AAFd7YWYQI6SdGd7zVfFAoFBNbeljG66EPI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8097790244"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "9860 1301 7507 6574")
CARD_OWNER = os.getenv("CARD_OWNER", "Javohir E")

TARIFFS = {
    "3": {"days": 3, "price": "10 000 so'm", "label": "3 kunlik"},
    "7": {"days": 7, "price": "20 000 so'm", "label": "1 haftalik"},
    "30": {"days": 30, "price": "40 000 so'm", "label": "1 oylik"},
}

logging.basicConfig(level=logging.INFO)
router = Router()


class Form(StatesGroup):
    waiting_code = State()
    waiting_admin_msg = State()
    waiting_receipt = State()
    waiting_search = State()


# ---------- Klaviaturalar ----------

def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Kino kodini kiriting", callback_data="code")
    kb.button(text="🔍 Kino qidirish", callback_data="search")
    kb.button(text="💬 Adminga yozish", callback_data="admin")
    kb.adjust(1)
    return kb.as_markup()


def back_kb(target):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Orqaga", callback_data=target)
    return kb.as_markup()


def vip_offer_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="💎 VIP sotib olish", callback_data="vip_menu")
    kb.button(text="⬅️ Orqaga", callback_data="main")
    kb.adjust(1)
    return kb.as_markup()


def vip_tariffs_kb():
    kb = InlineKeyboardBuilder()
    for key, t in TARIFFS.items():
        kb.button(text=f"{t['label']} — {t['price']}", callback_data=f"tariff:{key}")
    kb.button(text="⬅️ Orqaga", callback_data="search")
    kb.adjust(1)
    return kb.as_markup()


def tariff_detail_kb(key):
    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Chek yuborish", callback_data=f"pay:{key}")
    kb.button(text="⬅️ Orqaga", callback_data="vip_menu")
    kb.adjust(1)
    return kb.as_markup()


def admin_decision_kb(user_id, key):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=f"appr:{user_id}:{key}")
    kb.button(text="❌ Rad etish", callback_data=f"rej:{user_id}")
    kb.adjust(2)
    return kb.as_markup()


# ---------- Asosiy menyu ----------

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    db.add_user_if_not_exists(message.from_user.id)
    await message.answer(
        "Assalomu alaykum! 🎬 Kino kanal botiga xush kelibsiz.\n\nQuyidagilardan birini tanlang:",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "main")
async def cb_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Bosh menyu:", reply_markup=main_menu_kb())
    await call.answer()


# ---------- Kino kodi ----------

@router.callback_query(F.data == "code")
async def cb_code(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_code)
    await call.message.edit_text("🎬 Kino kodini kiriting:", reply_markup=back_kb("main"))
    await call.answer()


@router.message(Form.waiting_code)
async def process_code(message: Message, state: FSMContext):
    code = message.text.strip()
    movie = db.get_movie_by_code(code)
    if movie:
        title, file_id, file_type = movie
        if file_type == "video":
            await message.answer_video(file_id, caption=f"🎬 {title}", reply_markup=back_kb("main"))
        else:
            await message.answer_document(file_id, caption=f"🎬 {title}", reply_markup=back_kb("main"))
    else:
        await message.answer("❌ Bunday kod topilmadi. Qaytadan urinib ko'ring:", reply_markup=back_kb("main"))


# ---------- Kino qidirish (VIP) ----------

@router.callback_query(F.data == "search")
async def cb_search(call: CallbackQuery, state: FSMContext):
    if db.is_vip(call.from_user.id):
        await state.set_state(Form.waiting_search)
        await call.message.edit_text("🔍 Kino nomini kiriting:", reply_markup=back_kb("main"))
    else:
        await call.message.edit_text(
            "🔍 Kino qidirish funksiyasi faqat VIP foydalanuvchilar uchun.\n\n💎 VIP xarid qiling:",
            reply_markup=vip_offer_kb(),
        )
    await call.answer()


@router.message(Form.waiting_search)
async def process_search(message: Message, state: FSMContext):
    results = db.search_movies(message.text.strip())
    if results:
        text = "Topilgan kinolar:\n\n" + "\n".join(f"🎬 {title} — kod: {code}" for code, title in results)
    else:
        text = "❌ Hech narsa topilmadi."
    await message.answer(text, reply_markup=back_kb("main"))


# ---------- VIP sotib olish ----------

@router.callback_query(F.data == "vip_menu")
async def cb_vip_menu(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("💎 VIP tarifni tanlang:", reply_markup=vip_tariffs_kb())
    await call.answer()


@router.callback_query(F.data.startswith("tariff:"))
async def cb_tariff(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    t = TARIFFS[key]
    text = (
        f"💎 {t['label']} — {t['price']}\n\n"
        f"💳 Karta raqami: {CARD_NUMBER}\n"
        f"👤 Egasi: {CARD_OWNER}\n\n"
        f"To'lovni amalga oshirib, chekni yuboring 👇"
    )
    await call.message.edit_text(text, reply_markup=tariff_detail_kb(key))
    await call.answer()


@router.callback_query(F.data.startswith("pay:"))
async def cb_pay(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    await state.set_state(Form.waiting_receipt)
    await state.update_data(tariff=key)
    await call.message.edit_text(
        "📤 To'lov chekining rasmini (screenshot) yuboring:",
        reply_markup=back_kb(f"tariff:{key}"),
    )
    await call.answer()


@router.message(Form.waiting_receipt, F.photo)
async def process_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("tariff")
    t = TARIFFS[key]
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
    caption = (
        f"🧾 Yangi chek!\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} ({username})\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"💎 Tarif: {t['label']} — {t['price']}"
    )
    await message.bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=caption,
        reply_markup=admin_decision_kb(message.from_user.id, key),
    )
    await message.answer(
        "✅ Chekingiz adminga yuborildi. Tekshirilgach xabar beramiz.",
        reply_markup=back_kb("main"),
    )
    await state.clear()


@router.message(Form.waiting_receipt)
async def process_receipt_wrong_type(message: Message):
    await message.answer("⚠️ Iltimos, chekni rasm (screenshot) ko'rinishida yuboring.")


# ---------- Admin: tasdiqlash / rad etish ----------

@router.callback_query(F.data.startswith("appr:"))
async def cb_approve(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Ruxsat yo'q", show_alert=True)
    _, user_id, key = call.data.split(":")
    user_id = int(user_id)
    t = TARIFFS[key]
    until = db.set_vip(user_id, t["days"])
    await call.bot.send_message(
        user_id,
        f"✅ To'lovingiz tasdiqlandi!\n💎 VIP muddat: {until.strftime('%d.%m.%Y %H:%M')} gacha.",
        reply_markup=back_kb("main"),
    )
    old_caption = call.message.caption or ""
    await call.message.edit_caption(caption=old_caption + "\n\n✅ TASDIQLANDI")
    await call.answer("Tasdiqlandi")


@router.callback_query(F.data.startswith("rej:"))
async def cb_reject(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Ruxsat yo'q", show_alert=True)
    _, user_id = call.data.split(":")
    user_id = int(user_id)
    await call.bot.send_message(
        user_id,
        "❌ To'lovingiz tasdiqlanmadi. Qayta urinib ko'ring yoki adminga yozing.",
        reply_markup=back_kb("main"),
    )
    old_caption = call.message.caption or ""
    await call.message.edit_caption(caption=old_caption + "\n\n❌ RAD ETILDI")
    await call.answer("Rad etildi")


# ---------- Adminga yozish ----------

@router.callback_query(F.data == "admin")
async def cb_admin(call: CallbackQuery, state: FSMContext):
    await state.set_state(Form.waiting_admin_msg)
    await call.message.edit_text("💬 Xabaringizni yozing, adminga yuboriladi:", reply_markup=back_kb("main"))
    await call.answer()


@router.message(Form.waiting_admin_msg)
async def process_admin_msg(message: Message, state: FSMContext):
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
    await message.bot.send_message(
        ADMIN_ID,
        f"✉️ Yangi xabar:\n👤 {message.from_user.full_name} ({username})\n🆔 {message.from_user.id}\n\n{message.text}",
    )
    await message.answer("✅ Xabaringiz yuborildi.", reply_markup=back_kb("main"))
    await state.clear()


# ---------- Admin: kino qo'shish ----------
# Admin video yoki fayl yuborsa va caption (izoh) qismiga kino kodini yozsa,
# bot uni avtomatik saqlaydi. Masalan caption: 101

@router.message(F.video | F.document)
async def admin_add_movie(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.caption:
        await message.answer("⚠️ Kino kodini caption (izoh) qismiga yozing. Masalan caption: 101")
        return
    code = message.caption.strip()
    if message.video:
        db.add_movie(code, code, message.video.file_id, "video")
    else:
        db.add_movie(code, code, message.document.file_id, "document")
    await message.answer(f"✅ Kino saqlandi. Kod: {code}")


async def main():
    db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
