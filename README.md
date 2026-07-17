# Kino kanal boti

## Bot qanday ishlaydi

1. Foydalanuvchi `/start` bosadi → menyu chiqadi:
   - 🎬 Kino kodini kiriting
   - 🔍 Kino qidirish (faqat VIP)
   - 💬 Adminga yozish
2. "Kino qidirish" bosilsa, VIP bo'lmagan foydalanuvchiga "VIP sotib olish" tugmasi chiqadi.
3. VIP tariflar: 3 kunlik (10 000 so'm), 1 haftalik (20 000 so'm), 1 oylik (40 000 so'm).
4. Tarif tanlansa — karta raqami va "Chek yuborish" tugmasi chiqadi.
5. Foydalanuvchi chek (rasm) yuborsa — bu sizga (adminga) boradi, "Tasdiqlash"/"Rad etish" tugmalari bilan.
6. Tasdiqlasangiz — foydalanuvchiga avtomatik VIP muddat beriladi.
7. Har bir bosqichda "⬅️ Orqaga" tugmasi bor.

## Kino qo'shish (keyinroq)

Botga (admin sifatida) video yoki fayl yuboring, **caption (izoh)** qismiga kino kodini yozing.
Masalan caption: `101`
Bot avtomatik saqlab oladi. Foydalanuvchi keyin "101" kodini yozganda o'sha video chiqadi.

## GitHubga joylashtirish

1. Eski repodagi barcha fayllarni o'chiring.
2. Shu papkadagi fayllarni (`bot.py`, `database.py`, `requirements.txt`, `Procfile`) shu repoga yuklang.
3. **MUHIM:** `bot.py` ichidagi token va admin ID hozircha zaxira sifatida yozilgan. Repo public bo'lsa, buni GitHubga yubormasdan oldin token ustidan yangi token oling (@BotFather → /revoke) va Railway'da Environment Variables orqali bering — pastga qarang.

## Railway sozlamalari

Railway loyihangizda **Variables** bo'limiga kiring va quyidagilarni qo'shing:

| Nomi | Qiymati |
|---|---|
| `BOT_TOKEN` | Bot tokeningiz |
| `ADMIN_ID` | `8097790244` |
| `CARD_NUMBER` | `9860 1301 7507 6574` |
| `CARD_OWNER` | `Javohir E` |

**Settings → Start Command** qismiga: `python bot.py`

Shundan keyin Deploy qiling — bot ishga tushadi.

## Eslatma

- Ma'lumotlar bazasi (`bot.db`) Railway konteyner qayta ishga tushganda ba'zan tozalanishi mumkin (agar Volume ulanmagan bo'lsa). Doimiy saqlash uchun Railway'da bir marta **Volume** ulab, uni loyiha papkasiga bog'lab qo'yish tavsiya etiladi — aytsangiz shuni ham sozlab beraman.
