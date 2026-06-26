from typing import Dict


def format_booking_info(booking: Dict) -> str:
    status_map = {
        "pending": "⏳ Kutilmoqda",
        "confirmed": "✅ Tasdiqlangan",
        "rejected": "❌ Rad etilgan"
    }
    status = status_map.get(booking.get('status', ''), "❓ Noma'lum")

    return (
        f"📋 *Bron #{booking['id']}*\n"
        f"🏡 Dacha: *{booking['dacha_name']}*\n"
        f"📅 {booking['start_date']} → {booking['end_date']}\n"
        f"💰 Jami: *{booking['total_price']:,} so'm*\n"
        f"💳 To'langan avans: *{booking['advance']:,} so'm*\n"
        f"📊 Holat: {status}"
    )


def format_dacha_info(dacha: Dict) -> str:
    return (
        f"🏡 *{dacha['name']}*\n\n"
        f"📝 {dacha['description']}\n\n"
        f"📍 Manzil: *{dacha['location']}*\n"
        f"💰 Narx: *{dacha['price']:,} so'm/kun*\n"
        f"💳 Avans (20%): *{int(dacha['price'] * 0.20):,} so'm*"
    )
