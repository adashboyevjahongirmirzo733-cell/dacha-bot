# 🏡 DACHA BRON BOT — O'RNATISH QO'LLANMASI

## BOT NIMA QILA OLADI?

### Mijozlar uchun:
- Dachalarni ko'rish (rasm, tavsif, narx, manzil)
- Rangdor kalendar orqali sana tanlash (🟢 bo'sh, 🔴 band)
- 1 kundan 4 kungacha bron qilish
- Ism, familiya, telefon raqam kiritish
- To'lov havolasiga o'tib avans to'lash (20%)
- Chek rasmini yuborish
- Bronlar tarixini ko'rish

### Admin (siz) uchun:
- Dacha qo'shish (nom, tavsif, narx, manzil, rasm)
- Dachalarni tahrirlash / o'chirish
- Bronlarni ko'rish va tasdiqlash / rad etish
- Tasdiqlanganda mijozga avtomatik xabar ketadi
- Statistika (daromad, bronlar soni)

---

## O'RNATISH (QADAM BA'QADAM)

### 1-qadam: Python o'rnatish
https://python.org/downloads dan Python 3.10+ yuklab oling

### 2-qadam: Fayllarni papkaga soling
Barcha fayllarni bitta papkaga ko'chiring:
```
dacha_bot/
  bot.py
  config.py
  database.py
  keyboards.py
  utils.py
  requirements.txt
```

### 3-qadam: Kutubxonalarni o'rnatish
Terminal / CMD oching va quyidagini yozing:
```
pip install python-telegram-bot==20.7
```

### 4-qadam: To'lov havolasini sozlash
`config.py` faylini oching va bu qatorni o'zgartiring:
```python
PAYMENT_LINK = "https://uzcard.uz/your-payment-link"
```
O'rniga Uzcard yoki Humo ilovangizdan olingan doimiy to'lov havolangizni qo'ying.

### 5-qadam: Botni ishga tushirish
Terminal / CMD da papkaga kiring va:
```
python bot.py
```

---

## SERVERDA ISHLATISH (BOT DOIM YONIQ TURISHI UCHUN)

### Variant 1: Railway.app (BEPUL, tavsiya etiladi)
1. https://railway.app ga kiring
2. GitHub account bilan kiring
3. "New Project" → "Deploy from GitHub"
4. Papkangizni GitHub ga yuklang
5. Deploy qiling — tayyor!

### Variant 2: VPS server
```bash
# Ubuntu serverda:
apt install python3 python3-pip
pip3 install python-telegram-bot==20.7
python3 bot.py &
```

### Variant 3: Render.com (bepul)
1. https://render.com ga kiring
2. Web Service yarating
3. Kodni yuklang, ishga tushiring

---

## BOT ISHGA TUSHGANDAN SO'NG

1. Telegramda botingizga `/start` yuboring
2. Admin sifatida siz "Admin menyu" ko'rasiz
3. Avval dacha qo'shing: "➕ Dacha qo'shish"
4. Mijozlar `/start` bosib bron qila boshlaydi

---

## SAVOL VA MUAMMOLAR UCHUN

Har qanday muammo bo'lsa, Claude AI ga murojaat qiling 😊
