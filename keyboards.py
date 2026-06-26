import calendar as cal
from datetime import date, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Optional


MONTH_NAMES_UZ = {
    1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
    5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
    9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
}

DAY_NAMES = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏡 Dachalarni ko'rish", callback_data="view_dachas")],
        [InlineKeyboardButton("📋 Mening bronlarim", callback_data="my_bookings")],
    ])


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Dacha qo'shish", callback_data="admin_add_dacha")],
        [InlineKeyboardButton("🏡 Dachalarni boshqarish", callback_data="admin_view_dachas")],
        [InlineKeyboardButton("📋 Bronlarni ko'rish", callback_data="admin_view_bookings")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")],
    ])


def dachas_keyboard(dachas: List[Dict]) -> InlineKeyboardMarkup:
    keyboard = []
    for d in dachas:
        keyboard.append([
            InlineKeyboardButton(
                f"🏡 {d['name']} — {d['price']:,} so'm/kun",
                callback_data=f"dacha_{d['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def calendar_keyboard(
    year: int,
    month: int,
    dacha_id: int,
    db,
    stage: str,
    start_date: Optional[date] = None
) -> InlineKeyboardMarkup:
    keyboard = []
    today = date.today()

    # Header: month name + navigation
    month_name = MONTH_NAMES_UZ[month]
    keyboard.append([
        InlineKeyboardButton(
            "◀️", callback_data=f"cal_prev_{year}_{month}_{stage}"
        ),
        InlineKeyboardButton(
            f"📅 {month_name} {year}",
            callback_data="cal_ignore"
        ),
        InlineKeyboardButton(
            "▶️", callback_data=f"cal_next_{year}_{month}_{stage}"
        ),
    ])

    # Day names header
    keyboard.append([
        InlineKeyboardButton(d, callback_data="cal_ignore") for d in DAY_NAMES
    ])

    # Get booked dates
    booked_days = db.get_booked_dates(dacha_id, year, month)

    # Calendar days
    _, days_in_month = cal.monthrange(year, month)
    first_weekday = cal.monthrange(year, month)[0]  # 0=Monday

    row = []
    # Empty cells before first day
    for _ in range(first_weekday):
        row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))

    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        is_booked = day in booked_days
        is_past = current_date < today

        if is_past:
            # Past dates — greyed out
            btn = InlineKeyboardButton(f"·{day}·", callback_data="cal_ignore")
        elif is_booked:
            # Booked — red
            btn = InlineKeyboardButton(f"🔴{day}", callback_data="cal_ignore")
        else:
            # Available — green
            if stage == "start":
                cb = f"date_start_{year}_{month}_{day}"
            else:
                # End date: highlight valid range (start+1 to start+4)
                if start_date:
                    days_diff = (current_date - start_date).days
                    if days_diff <= 0 or days_diff > 4:
                        btn = InlineKeyboardButton(f"·{day}·", callback_data="cal_ignore")
                        row.append(btn)
                        if len(row) == 7:
                            keyboard.append(row)
                            row = []
                        continue
                cb = f"date_end_{year}_{month}_{day}"
            btn = InlineKeyboardButton(f"🟢{day}", callback_data=cb)

        row.append(btn)
        if len(row) == 7:
            keyboard.append(row)
            row = []

    # Fill remaining cells
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
        keyboard.append(row)

    # Back button
    if stage == "start":
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_dacha")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")])

    return InlineKeyboardMarkup(keyboard)


def confirm_booking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash va to'lash", callback_data="confirm_booking")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_booking")],
    ])


def admin_bookings_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{booking_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{booking_id}"),
        ]
    ])
