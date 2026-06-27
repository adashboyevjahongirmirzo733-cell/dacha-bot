import calendar as cal
from datetime import date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MONTHS = {1:"Yanvar",2:"Fevral",3:"Mart",4:"Aprel",5:"May",6:"Iyun",
          7:"Iyul",8:"Avgust",9:"Sentabr",10:"Oktabr",11:"Noyabr",12:"Dekabr"}
DAYS = ["Du","Se","Ch","Pa","Ju","Sh","Ya"]


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏡 Dachalarni ko'rish", callback_data="dachas")],
        [InlineKeyboardButton("📋 Mening bronlarim", callback_data="my_bookings")],
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Dacha qo'shish", callback_data="add_dacha")],
        [InlineKeyboardButton("🏡 Dachalarni boshqarish", callback_data="manage_dachas")],
        [InlineKeyboardButton("📋 Bronlar", callback_data="all_bookings")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
    ])


def dachas_kb(dachas):
    kb = [[InlineKeyboardButton(f"🏡 {d['name']} — {d['price']:,} so'm/kun",
           callback_data=f"d_{d['id']}")] for d in dachas]
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def calendar_kb(year, month, dacha_id, db, stage, start_date=None):
    kb = []
    today = date.today()

    kb.append([
        InlineKeyboardButton("◀️", callback_data=f"cp_{year}_{month}_{stage}_{dacha_id}"),
        InlineKeyboardButton(f"📅 {MONTHS[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton("▶️", callback_data=f"cn_{year}_{month}_{stage}_{dacha_id}"),
    ])
    kb.append([InlineKeyboardButton(d, callback_data="ignore") for d in DAYS])

    booked = db.booked_days(dacha_id, year, month)
    _, days_in_month = cal.monthrange(year, month)
    first_day = cal.monthrange(year, month)[0]

    row = [InlineKeyboardButton(" ", callback_data="ignore") for _ in range(first_day)]

    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        if d < today or day in booked:
            btn = InlineKeyboardButton(f"🔴{day}" if day in booked else f"·{day}·", callback_data="ignore")
        else:
            if stage == "start":
                btn = InlineKeyboardButton(f"🟢{day}", callback_data=f"ds_{year}_{month}_{day}_{dacha_id}")
            else:
                if start_date:
                    diff = (d - start_date).days
                    if diff <= 0 or diff > 4:
                        btn = InlineKeyboardButton(f"·{day}·", callback_data="ignore")
                    else:
                        btn = InlineKeyboardButton(f"🟢{day}", callback_data=f"de_{year}_{month}_{day}_{dacha_id}")
                else:
                    btn = InlineKeyboardButton(f"🟢{day}", callback_data=f"de_{year}_{month}_{day}_{dacha_id}")

        row.append(btn)
        if len(row) == 7:
            kb.append(row)
            row = []

    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        kb.append(row)

    back = "back_dachas" if stage == "start" else f"back_start_{dacha_id}"
    kb.append([InlineKeyboardButton("🔙 Orqaga", callback_data=back)])
    return InlineKeyboardMarkup(kb)


def booking_confirm_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data="do_confirm")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
    ])


def payment_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Chek rasmini yuborish", callback_data="send_receipt")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")],
    ])


def admin_booking_kb(booking_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{booking_id}"),
         InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{booking_id}")],
    ])
