import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from config import BOT_TOKEN, ADMIN_ID, PAYMENT_LINK
from keyboards import (
    main_menu_keyboard, admin_menu_keyboard,
    calendar_keyboard, dachas_keyboard,
    confirm_booking_keyboard, admin_bookings_keyboard
)
from utils import format_booking_info, format_dacha_info
import calendar as cal
from datetime import datetime, date

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# States
(
    MAIN_MENU,
    SELECT_DACHA,
    SELECT_START_DATE,
    SELECT_END_DATE,
    ENTER_NAME,
    ENTER_PHONE,
    CONFIRM_BOOKING,
    UPLOAD_RECEIPT,
    # Admin states
    ADMIN_MENU,
    ADMIN_ADD_DACHA_NAME,
    ADMIN_ADD_DACHA_DESC,
    ADMIN_ADD_DACHA_PRICE,
    ADMIN_ADD_DACHA_PHOTO,
    ADMIN_ADD_DACHA_LOCATION,
) = range(14)


# ============================================================
# START
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()

    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👋 Xush kelibsiz, Admin!\n\nNima qilmoqchisiz?",
            reply_markup=admin_menu_keyboard()
        )
        return ADMIN_MENU

    await update.message.reply_text(
        "🏡 *Dacha Bron — Xush kelibsiz!*\n\n"
        "Tabiat qo'ynida dam olish uchun dachalarimizni ko'ring va bron qiling.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU


# ============================================================
# MAIN MENU
# ============================================================
async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "view_dachas":
        dachas = db.get_all_dachas()
        if not dachas:
            await query.edit_message_text(
                "😔 Hozircha hech qanday dacha qo'shilmagan.\nKo'proq dachalar tez orada qo'shiladi!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")
                ]])
            )
            return MAIN_MENU

        await query.edit_message_text(
            "🏡 *Mavjud dachalar*\n\nKo'rmoqchi bo'lgan dachani tanlang:",
            parse_mode="Markdown",
            reply_markup=dachas_keyboard(dachas)
        )
        return SELECT_DACHA

    elif data == "my_bookings":
        user_id = update.effective_user.id
        bookings = db.get_user_bookings(user_id)
        if not bookings:
            await query.edit_message_text(
                "📋 Sizda hali hech qanday bron yo'q.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")
                ]])
            )
            return MAIN_MENU

        text = "📋 *Sizning bronlaringiz:*\n\n"
        for b in bookings:
            text += format_booking_info(b) + "\n---\n"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")
            ]])
        )
        return MAIN_MENU

    elif data == "back_main":
        await query.edit_message_text(
            "🏡 *Dacha Bron — Asosiy menyu*",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU


# ============================================================
# DACHA SELECTION
# ============================================================
async def select_dacha_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        await query.edit_message_text(
            "🏡 *Dacha Bron — Asosiy menyu*",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU

    if data.startswith("dacha_"):
        dacha_id = int(data.split("_")[1])
        dacha = db.get_dacha(dacha_id)
        if not dacha:
            await query.answer("Dacha topilmadi!", show_alert=True)
            return SELECT_DACHA

        context.user_data['dacha_id'] = dacha_id
        context.user_data['dacha'] = dacha

        text = format_dacha_info(dacha)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Bron qilish", callback_data=f"book_{dacha_id}")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_dachas")]
        ])

        if dacha.get('photo_id'):
            try:
                await query.message.delete()
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=dacha['photo_id'],
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            except Exception:
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

        return SELECT_DACHA

    if data.startswith("book_"):
        dacha_id = int(data.split("_")[1])
        context.user_data['dacha_id'] = dacha_id

        now = datetime.now()
        markup = calendar_keyboard(now.year, now.month, dacha_id, db, "start")

        try:
            await query.edit_message_caption(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception:
            await query.edit_message_text(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return SELECT_START_DATE

    if data == "back_dachas":
        dachas = db.get_all_dachas()
        await query.edit_message_text(
            "🏡 *Mavjud dachalar*\n\nKo'rmoqchi bo'lgan dachani tanlang:",
            parse_mode="Markdown",
            reply_markup=dachas_keyboard(dachas)
        )
        return SELECT_DACHA


# ============================================================
# CALENDAR — START DATE
# ============================================================
async def select_start_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    dacha_id = context.user_data.get('dacha_id')

    if data.startswith("cal_prev_") or data.startswith("cal_next_"):
        parts = data.split("_")
        direction = parts[1]
        year = int(parts[2])
        month = int(parts[3])
        stage = parts[4]

        if direction == "prev":
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        else:
            month += 1
            if month == 13:
                month = 1
                year += 1

        markup = calendar_keyboard(year, month, dacha_id, db, stage)
        try:
            await query.edit_message_caption(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception:
            await query.edit_message_text(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return SELECT_START_DATE

    if data.startswith("date_start_"):
        parts = data.split("_")
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])

        selected_date = date(year, month, day)
        today = date.today()

        if selected_date < today:
            await query.answer("⚠️ O'tgan sanani tanlab bo'lmaydi!", show_alert=True)
            return SELECT_START_DATE

        if db.is_date_booked(dacha_id, selected_date):
            await query.answer("🔴 Bu sana band!", show_alert=True)
            return SELECT_START_DATE

        context.user_data['start_date'] = selected_date
        markup = calendar_keyboard(year, month, dacha_id, db, "end", start_date=selected_date)

        try:
            await query.edit_message_caption(
                f"✅ Kirish: *{selected_date.strftime('%d.%m.%Y')}*\n\n"
                "📅 *Chiqish sanasini tanlang:*\n_(maksimal 4 kun)_\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception:
            await query.edit_message_text(
                f"✅ Kirish: *{selected_date.strftime('%d.%m.%Y')}*\n\n"
                "📅 *Chiqish sanasini tanlang:*\n_(maksimal 4 kun)_\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return SELECT_END_DATE

    if data == "cal_ignore":
        return SELECT_START_DATE

    if data == "back_dacha":
        dachas = db.get_all_dachas()
        try:
            await query.edit_message_caption(
                "🏡 *Mavjud dachalar*",
                parse_mode="Markdown",
                reply_markup=dachas_keyboard(dachas)
            )
        except Exception:
            await query.edit_message_text(
                "🏡 *Mavjud dachalar*",
                parse_mode="Markdown",
                reply_markup=dachas_keyboard(dachas)
            )
        return SELECT_DACHA


# ============================================================
# CALENDAR — END DATE
# ============================================================
async def select_end_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    dacha_id = context.user_data.get('dacha_id')
    start_date = context.user_data.get('start_date')

    if data.startswith("cal_prev_") or data.startswith("cal_next_"):
        parts = data.split("_")
        direction = parts[1]
        year = int(parts[2])
        month = int(parts[3])

        if direction == "prev":
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        else:
            month += 1
            if month == 13:
                month = 1
                year += 1

        markup = calendar_keyboard(year, month, dacha_id, db, "end", start_date=start_date)
        try:
            await query.edit_message_caption(
                f"✅ Kirish: *{start_date.strftime('%d.%m.%Y')}*\n\n"
                "📅 *Chiqish sanasini tanlang:*\n_(maksimal 4 kun)_\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception:
            await query.edit_message_text(
                f"✅ Kirish: *{start_date.strftime('%d.%m.%Y')}*\n\n"
                "📅 *Chiqish sanasini tanlang:*\n_(maksimal 4 kun)_\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return SELECT_END_DATE

    if data.startswith("date_end_"):
        parts = data.split("_")
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])

        end_date = date(year, month, day)

        if end_date <= start_date:
            await query.answer("⚠️ Chiqish sanasi kirish sanasidan keyin bo'lishi kerak!", show_alert=True)
            return SELECT_END_DATE

        days = (end_date - start_date).days
        if days > 4:
            await query.answer("⚠️ Maksimal bron muddati 4 kun!", show_alert=True)
            return SELECT_END_DATE

        # Check all dates in range are free
        for i in range(days):
            check_date = date.fromordinal(start_date.toordinal() + i)
            if db.is_date_booked(dacha_id, check_date):
                await query.answer(f"🔴 {check_date.strftime('%d.%m')} sanasi band!", show_alert=True)
                return SELECT_END_DATE

        context.user_data['end_date'] = end_date
        context.user_data['days'] = days

        try:
            await query.edit_message_caption(
                "👤 *Ism va familiyangizni kiriting:*\n\n_Misol: Ahmadov Jasur_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")
                ]])
            )
        except Exception:
            await query.edit_message_text(
                "👤 *Ism va familiyangizni kiriting:*\n\n_Misol: Ahmadov Jasur_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")
                ]])
            )
        return ENTER_NAME

    if data == "cal_ignore":
        return SELECT_END_DATE

    if data == "back_start":
        now = datetime.now()
        markup = calendar_keyboard(now.year, now.month, dacha_id, db, "start")
        try:
            await query.edit_message_caption(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception:
            await query.edit_message_text(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
        return SELECT_START_DATE


# ============================================================
# ENTER NAME
# ============================================================
async def enter_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "back_start":
            dacha_id = context.user_data.get('dacha_id')
            now = datetime.now()
            markup = calendar_keyboard(now.year, now.month, dacha_id, db, "start")
            await query.edit_message_text(
                "📅 *Kirish sanasini tanlang:*\n\n🟢 Bo'sh  🔴 Band",
                parse_mode="Markdown",
                reply_markup=markup
            )
            return SELECT_START_DATE
        return ENTER_NAME

    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("⚠️ Iltimos, to'liq ism familiyangizni kiriting.")
        return ENTER_NAME

    context.user_data['name'] = name
    await update.message.reply_text(
        "📞 *Telefon raqamingizni kiriting:*\n\n_Misol: +998901234567_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Orqaga", callback_data="back_name")
        ]])
    )
    return ENTER_PHONE


# ============================================================
# ENTER PHONE
# ============================================================
async def enter_phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "back_name":
            await query.edit_message_text(
                "👤 *Ism va familiyangizni kiriting:*\n\n_Misol: Ahmadov Jasur_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")
                ]])
            )
            return ENTER_NAME
        return ENTER_PHONE

    phone = update.message.text.strip()
    phone = phone.replace(" ", "").replace("-", "")
    if not (phone.startswith("+998") or phone.startswith("998") or phone.startswith("0")):
        await update.message.reply_text(
            "⚠️ Iltimos, to'g'ri telefon raqam kiriting.\n_Misol: +998901234567_",
            parse_mode="Markdown"
        )
        return ENTER_PHONE

    context.user_data['phone'] = phone

    # Show booking summary
    dacha_id = context.user_data['dacha_id']
    dacha = db.get_dacha(dacha_id)
    start_date = context.user_data['start_date']
    end_date = context.user_data['end_date']
    days = context.user_data['days']
    name = context.user_data['name']

    total_price = dacha['price'] * days
    advance = int(total_price * 0.20)

    context.user_data['total_price'] = total_price
    context.user_data['advance'] = advance

    text = (
        f"📋 *Bron ma'lumotlari:*\n\n"
        f"🏡 Dacha: *{dacha['name']}*\n"
        f"📅 Kirish: *{start_date.strftime('%d.%m.%Y')}*\n"
        f"📅 Chiqish: *{end_date.strftime('%d.%m.%Y')}*\n"
        f"🌙 Kunlar soni: *{days} kun*\n"
        f"👤 Ism: *{name}*\n"
        f"📞 Tel: *{phone}*\n\n"
        f"💰 Jami narx: *{total_price:,} so'm*\n"
        f"💳 Avans (20%): *{advance:,} so'm*\n\n"
        f"_Avansni to'lashingiz kerak. To'lov tasdiqlangach bron yakunlanadi._"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=confirm_booking_keyboard()
    )
    return CONFIRM_BOOKING


# ============================================================
# CONFIRM BOOKING
# ============================================================
async def confirm_booking_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "confirm_booking":
        await query.edit_message_text(
            f"💳 *To'lov qilish*\n\n"
            f"Avans miqdori: *{context.user_data['advance']:,} so'm*\n\n"
            f"Quyidagi tugma orqali to'lovni amalga oshiring, so'ngra chek rasmini yuboring:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 To'lov qilish", url=PAYMENT_LINK)],
                [InlineKeyboardButton("📸 Chek rasmini yuborish", callback_data="send_receipt")],
                [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_booking")]
            ])
        )
        return CONFIRM_BOOKING

    elif data == "send_receipt":
        await query.edit_message_text(
            "📸 *Chek rasmini yuboring:*\n\n"
            "_To'lov chekining rasmini shu yerga yuboring_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="confirm_booking")
            ]])
        )
        return UPLOAD_RECEIPT

    elif data == "cancel_booking":
        context.user_data.clear()
        await query.edit_message_text(
            "❌ Bron bekor qilindi.\n\n🏡 Asosiy menyuga qaytdingiz.",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU


# ============================================================
# UPLOAD RECEIPT
# ============================================================
async def upload_receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text(
            "⚠️ Iltimos, chek *rasmini* yuboring (faqat rasm).",
            parse_mode="Markdown"
        )
        return UPLOAD_RECEIPT

    photo = update.message.photo[-1]
    user_id = update.effective_user.id
    username = update.effective_user.username or "Yo'q"

    dacha_id = context.user_data['dacha_id']
    dacha = db.get_dacha(dacha_id)
    start_date = context.user_data['start_date']
    end_date = context.user_data['end_date']
    days = context.user_data['days']
    name = context.user_data['name']
    phone = context.user_data['phone']
    total_price = context.user_data['total_price']
    advance = context.user_data['advance']

    # Save booking to DB
    booking_id = db.create_booking(
        user_id=user_id,
        dacha_id=dacha_id,
        start_date=start_date,
        end_date=end_date,
        name=name,
        phone=phone,
        total_price=total_price,
        advance=advance,
        receipt_photo_id=photo.file_id,
        status="pending"
    )

    # Notify admin
    admin_text = (
        f"🔔 *Yangi bron #{booking_id}*\n\n"
        f"🏡 Dacha: *{dacha['name']}*\n"
        f"📅 Kirish: *{start_date.strftime('%d.%m.%Y')}*\n"
        f"📅 Chiqish: *{end_date.strftime('%d.%m.%Y')}*\n"
        f"🌙 Kunlar: *{days} kun*\n"
        f"👤 Ism: *{name}*\n"
        f"📞 Tel: *{phone}*\n"
        f"💬 Username: @{username}\n\n"
        f"💰 Jami: *{total_price:,} so'm*\n"
        f"💳 Avans: *{advance:,} so'm*\n\n"
        f"📸 Chek rasmini ko'rish uchun yuqoridagi rasm"
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_bookings_keyboard(booking_id)
        )
    except Exception as e:
        logger.error(f"Admin notification error: {e}")

    await update.message.reply_text(
        f"✅ *Chek yuborildi!*\n\n"
        f"Bron #{booking_id} ko'rib chiqilmoqda.\n"
        f"Admin tasdiqlashi bilanoq sizga xabar yuboriladi.\n\n"
        f"_Odatda 30 daqiqa ichida tasdiqlanadi._",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU


# ============================================================
# ADMIN MENU
# ============================================================
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_add_dacha":
        await query.edit_message_text(
            "🏡 *Yangi dacha qo'shish*\n\n"
            "1-qadam: Dacha nomini kiriting:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel")
            ]])
        )
        return ADMIN_ADD_DACHA_NAME

    elif data == "admin_view_dachas":
        dachas = db.get_all_dachas()
        if not dachas:
            await query.edit_message_text(
                "📋 Hali hech qanday dacha qo'shilmagan.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("➕ Dacha qo'shish", callback_data="admin_add_dacha"),
                    InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
                ]])
            )
            return ADMIN_MENU

        text = "🏡 *Barcha dachalar:*\n\n"
        keyboard = []
        for d in dachas:
            text += f"• {d['name']} — {d['price']:,} so'm/kun\n"
            keyboard.append([
                InlineKeyboardButton(f"✏️ {d['name']}", callback_data=f"admin_edit_{d['id']}"),
                InlineKeyboardButton("🗑", callback_data=f"admin_delete_{d['id']}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")])

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_MENU

    elif data == "admin_view_bookings":
        bookings = db.get_all_bookings()
        if not bookings:
            await query.edit_message_text(
                "📋 Hali hech qanday bron yo'q.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
                ]])
            )
            return ADMIN_MENU

        text = "📋 *Barcha bronlar:*\n\n"
        keyboard = []
        for b in bookings:
            status_emoji = {"pending": "⏳", "confirmed": "✅", "rejected": "❌"}.get(b['status'], "❓")
            text += f"{status_emoji} #{b['id']} — {b['dacha_name']} | {b['start_date']} → {b['end_date']}\n👤 {b['name']} | 📞 {b['phone']}\n\n"
            if b['status'] == 'pending':
                keyboard.append([
                    InlineKeyboardButton(f"✅ #{b['id']} tasdiqlash", callback_data=f"approve_{b['id']}"),
                    InlineKeyboardButton(f"❌ Rad etish", callback_data=f"reject_{b['id']}")
                ])

        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")])

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ADMIN_MENU

    elif data == "admin_stats":
        stats = db.get_stats()
        text = (
            f"📊 *Statistika:*\n\n"
            f"🏡 Dachalar soni: *{stats['dachas']}*\n"
            f"📋 Jami bronlar: *{stats['total_bookings']}*\n"
            f"✅ Tasdiqlangan: *{stats['confirmed']}*\n"
            f"⏳ Kutilmoqda: *{stats['pending']}*\n"
            f"❌ Rad etilgan: *{stats['rejected']}*\n"
            f"💰 Jami daromad: *{stats['total_revenue']:,} so'm*"
        )
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")
            ]])
        )
        return ADMIN_MENU

    elif data.startswith("approve_"):
        booking_id = int(data.split("_")[1])
        booking = db.get_booking(booking_id)
        if booking:
            db.update_booking_status(booking_id, "confirmed")
            try:
                await context.bot.send_message(
                    chat_id=booking['user_id'],
                    text=f"🎉 *Tabriklaymiz!*\n\n"
                         f"Bron #{booking_id} tasdiqlandi!\n\n"
                         f"🏡 Dacha: *{booking['dacha_name']}*\n"
                         f"📅 Kirish: *{booking['start_date']}*\n"
                         f"📅 Chiqish: *{booking['end_date']}*\n\n"
                         f"_Xush kelibsiz!_ 🌿",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"User notification error: {e}")

            await query.answer("✅ Bron tasdiqlandi!", show_alert=True)
            await query.edit_message_caption(
                query.message.caption + "\n\n✅ *TASDIQLANDI*",
                parse_mode="Markdown"
            )
        return ADMIN_MENU

    elif data.startswith("reject_"):
        booking_id = int(data.split("_")[1])
        booking = db.get_booking(booking_id)
        if booking:
            db.update_booking_status(booking_id, "rejected")
            try:
                await context.bot.send_message(
                    chat_id=booking['user_id'],
                    text=f"😔 Bron #{booking_id} rad etildi.\n\n"
                         f"Savollar uchun bog'laning.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"User notification error: {e}")

            await query.answer("❌ Bron rad etildi!", show_alert=True)
            try:
                await query.edit_message_caption(
                    query.message.caption + "\n\n❌ *RAD ETILDI*",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
        return ADMIN_MENU

    elif data.startswith("admin_delete_"):
        dacha_id = int(data.split("_")[2])
        dacha = db.get_dacha(dacha_id)
        await query.edit_message_text(
            f"⚠️ *{dacha['name']}* ni o'chirmoqchimisiz?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"admin_confirm_delete_{dacha_id}"),
                    InlineKeyboardButton("❌ Yo'q", callback_data="admin_view_dachas")
                ]
            ])
        )
        return ADMIN_MENU

    elif data.startswith("admin_confirm_delete_"):
        dacha_id = int(data.split("_")[3])
        db.delete_dacha(dacha_id)
        await query.answer("🗑 Dacha o'chirildi!", show_alert=True)
        await query.edit_message_text(
            "👋 Xush kelibsiz, Admin!",
            reply_markup=admin_menu_keyboard()
        )
        return ADMIN_MENU

    elif data == "admin_back" or data == "admin_cancel":
        await query.edit_message_text(
            "👋 Admin menyu:",
            reply_markup=admin_menu_keyboard()
        )
        return ADMIN_MENU


# ============================================================
# ADMIN ADD DACHA STEPS
# ============================================================
async def admin_add_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "admin_cancel":
            await query.edit_message_text("👋 Admin menyu:", reply_markup=admin_menu_keyboard())
            return ADMIN_MENU
        return ADMIN_ADD_DACHA_NAME

    context.user_data['new_dacha_name'] = update.message.text.strip()
    await update.message.reply_text(
        "2-qadam: Dacha tavsifini kiriting:\n\n_Misol: 3 xonali, hovuz bor, 10 kishi sig'adi..._",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel")
        ]])
    )
    return ADMIN_ADD_DACHA_DESC


async def admin_add_desc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "admin_cancel":
            await query.edit_message_text("👋 Admin menyu:", reply_markup=admin_menu_keyboard())
            return ADMIN_MENU
        return ADMIN_ADD_DACHA_DESC

    context.user_data['new_dacha_desc'] = update.message.text.strip()
    await update.message.reply_text(
        "3-qadam: Kunlik narxini kiriting (so'mda):\n\n_Misol: 500000_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel")
        ]])
    )
    return ADMIN_ADD_DACHA_PRICE


async def admin_add_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "admin_cancel":
            await query.edit_message_text("👋 Admin menyu:", reply_markup=admin_menu_keyboard())
            return ADMIN_MENU
        return ADMIN_ADD_DACHA_PRICE

    try:
        price = int(update.message.text.strip().replace(",", "").replace(" ", ""))
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ Iltimos, to'g'ri narx kiriting (faqat raqam).")
        return ADMIN_ADD_DACHA_PRICE

    context.user_data['new_dacha_price'] = price
    await update.message.reply_text(
        "4-qadam: Manzilini kiriting:\n\n_Misol: Toshkent viloyati, Bo'stonliq tumani_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel")
        ]])
    )
    return ADMIN_ADD_DACHA_LOCATION


async def admin_add_location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "admin_cancel":
            await query.edit_message_text("👋 Admin menyu:", reply_markup=admin_menu_keyboard())
            return ADMIN_MENU
        return ADMIN_ADD_DACHA_LOCATION

    context.user_data['new_dacha_location'] = update.message.text.strip()
    await update.message.reply_text(
        "5-qadam: Dacha rasmini yuboring:\n\n_(Rasm yubormaslik uchun /skip bosing)_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Rasmisiz davom etish", callback_data="skip_photo")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_cancel")]
        ])
    )
    return ADMIN_ADD_DACHA_PHOTO


async def admin_add_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_id = None

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data == "admin_cancel":
            await query.edit_message_text("👋 Admin menyu:", reply_markup=admin_menu_keyboard())
            return ADMIN_MENU
        if query.data == "skip_photo":
            photo_id = None
        else:
            return ADMIN_ADD_DACHA_PHOTO
    elif update.message.photo:
        photo_id = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("⚠️ Rasm yuboring yoki 'Rasmisiz davom etish' tugmasini bosing.")
        return ADMIN_ADD_DACHA_PHOTO

    # Save dacha
    dacha_id = db.add_dacha(
        name=context.user_data['new_dacha_name'],
        description=context.user_data['new_dacha_desc'],
        price=context.user_data['new_dacha_price'],
        location=context.user_data['new_dacha_location'],
        photo_id=photo_id
    )

    success_text = (
        f"✅ *Dacha muvaffaqiyatli qo'shildi!*\n\n"
        f"🏡 Nom: *{context.user_data['new_dacha_name']}*\n"
        f"📍 Manzil: *{context.user_data['new_dacha_location']}*\n"
        f"💰 Narx: *{context.user_data['new_dacha_price']:,} so'm/kun*"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            success_text,
            parse_mode="Markdown",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            success_text,
            parse_mode="Markdown",
            reply_markup=admin_menu_keyboard()
        )

    context.user_data.clear()
    return ADMIN_MENU


# ============================================================
# MAIN
# ============================================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_handler)],
            SELECT_DACHA: [CallbackQueryHandler(select_dacha_handler)],
            SELECT_START_DATE: [CallbackQueryHandler(select_start_date_handler)],
            SELECT_END_DATE: [CallbackQueryHandler(select_end_date_handler)],
            ENTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name_handler),
                CallbackQueryHandler(enter_name_handler)
            ],
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone_handler),
                CallbackQueryHandler(enter_phone_handler)
            ],
            CONFIRM_BOOKING: [CallbackQueryHandler(confirm_booking_handler)],
            UPLOAD_RECEIPT: [
                MessageHandler(filters.PHOTO, upload_receipt_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, upload_receipt_handler),
            ],
            ADMIN_MENU: [CallbackQueryHandler(admin_menu_handler)],
            ADMIN_ADD_DACHA_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_name_handler),
                CallbackQueryHandler(admin_add_name_handler)
            ],
            ADMIN_ADD_DACHA_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_desc_handler),
                CallbackQueryHandler(admin_add_desc_handler)
            ],
            ADMIN_ADD_DACHA_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_price_handler),
                CallbackQueryHandler(admin_add_price_handler)
            ],
            ADMIN_ADD_DACHA_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_location_handler),
                CallbackQueryHandler(admin_add_location_handler)
            ],
            ADMIN_ADD_DACHA_PHOTO: [
                MessageHandler(filters.PHOTO, admin_add_photo_handler),
                CallbackQueryHandler(admin_add_photo_handler)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_message=False,
        allow_reentry=True,
    )

    app.add_handler(conv_handler)

    print("🤖 Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
