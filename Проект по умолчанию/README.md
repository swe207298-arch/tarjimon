# 🌍 5 tilli tarjimon Telegram bot

Istalgan tilda matn yuboring — bot tilni **avtomatik aniqlaydi**, so‘ng chiroyli tugmalar orqali
**5 tildan birini** tanlab tarjima qilasiz.

| Til | Bayroq |
| --- | --- |
| Ingliz | 🇬🇧 |
| Rus | 🇷🇺 |
| Arab | 🇸🇦 |
| Xitoy | 🇨🇳 |
| O‘zbek | 🇺🇿 |

## ✨ Imkoniyatlar

- 🔍 Matn tilini avtomatik aniqlash (Google Translate asosida + zaxira taxmin).
- 🌐 5 tilga tarjima: ingliz, rus, arab, xitoy, o‘zbek.
- 🎛 Matn yuborilgach, darhol **til tanlash tugmalari** chiqadi.
- 💬 Chiroyli HTML formatlash: sarlavhalar, iqtibos bloklari, bayroqlar.
- 📄 Uzun matnlarni avtomatik qismlarga bo‘lib tarjima qilish.
- 🛠 **Admin panel**:
  - 📢 **E’lon** — istalgan kontentni barcha foydalanuvchilarga yuborish.
  - 📣 **Reklama** — kontent + havolali tugma bilan yuborish.
  - 📌 **Majburiy kanal** — foydalanuvchi obuna bo‘lmaguncha botdan foydalana olmaydi.
  - 📊 Statistika: jami/bugungi foydalanuvchilar, tarjimalar, kanallar.
- 🚫 Obuna bo‘lmagan foydalanuvchiga «✅ Tekshirish» tugmasi bilan eslatma.

## 📁 Loyiha tuzilishi

```
bot.py                      # Kirish nuqtasi
config.py                   # .env sozlamalari
database.py                 # SQLite (foydalanuvchilar, tarjimalar, kanallar)
translator.py               # Tilni aniqlash va tarjima qilish
keyboards.py                # Inline tugmalar
texts.py                    # Barcha matnlar
utils.py                    # HTML xavfsizlik va matn bo‘lish
handlers/
  user.py                   # Foydalanuvchi oqimi
  admin.py                  # Admin panel
middlewares/
  subscription.py           # Majburiy kanal tekshiruvi
```

## 🚀 O‘rnatish (Windows)

> Talab: **Python 3.10+** (3.11 yoki 3.12 tavsiya etiladi).

### 1-usul: `start.bat`

1. `.env.example` faylidan nusxa olib, nomini `.env` qiling.
2. `.env` ichida `BOT_TOKEN` va `ADMIN_IDS` ni to‘ldiring.
3. `start.bat` faylini ikki marta bosing — u virtual muhit yaratadi, kutubxonalarni o‘rnatadi va botni ishga tushiradi.

### 2-usul: qo‘lda

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

## ⚙️ `.env` sozlash

```env
BOT_TOKEN=1234567890:AA...        # @BotFather dan
ADMIN_IDS=123456789               # @userinfobot dan (bir nechta bo‘lsa vergul bilan)
DB_PATH=data/bot.db
REQUEST_TIMEOUT=20
BROADCAST_DELAY=0.05
```

- **BOT_TOKEN** — Telegram’da [@BotFather](https://t.me/BotFather) → `/newbot` orqali olinadi.
- **ADMIN_IDS** — o‘z Telegram ID ingiz. Bir nechta admin: `ADMIN_IDS=111,222,333`.

## 🛠 Admin panel

Admin `/admin` buyrug‘ini yuboradi (yoki `/start` xabaridagi havola orqali):

| Bo‘lim | Vazifasi |
| --- | --- |
| 📢 E’lon yuborish | Matn/rasm/video — barcha foydalanuvchilarga `copy_message` orqali yuboriladi. |
| 📣 Reklama yuborish | Avval kontent, keyin `Tugma matni \| https://havola` formatida tugma. Tugmasiz: `/skip`. |
| 📌 Majburiy kanallar | Kanal qo‘shish/o‘chirish va obunani tekshirish. |
| 📊 Statistika | Foydalanuvchilar va tarjimalar soni. |

### Majburiy kanal qo‘shish

1. Botni kanalga **administrator** qilib qo‘shing.
2. Botga **«Taklif havolalari»** huquqini bering.
3. Admin panel → **📌 Majburiy kanallar** → **➕ Kanal qo‘shish**.
4. `@kanal_username`, `https://t.me/kanal` yoki kanaldan forward qilingan xabar yuboring.

Shundan so‘ng barcha foydalanuvchilar avval kanal(lar)ga obuna bo‘lishi shart bo‘ladi.
Adminlar bu tekshiruvdan ozod.

## 💡 Eslatmalar

- Tarjima **Google Translate’ning bepul (kalitsiz) endpointi** orqali ishlaydi.
  Rasmiy kafolat yo‘q; agar barqarorlik muhim bo‘lsa, `translator.py` ni rasmiy
  Google Cloud Translation yoki DeepL API ga almashtirish mumkin.
- Telegram o‘z shriftlarini cheklaydi, shuning uchun «chiroyli shrift» sifatida
  **bold**, *italic*, `<blockquote>` va emoji’lardan foydalanilgan.
- Foydalanuvchi matnlari bazada faqat **2 kun** saqlanadi (tugmalar ishlashi uchun),
  keyin avtomatik o‘chiriladi.
- Baza: `data/bot.db` (SQLite, alohida server talab qilmaydi).
- Botni 24/7 ishlatish uchun VPS yoki `systemd`/`pm2` kabi xizmatlardan foydalaning.

## 🤖 Buyruqlar

| Buyruq | Kim uchun | Vazifasi |
| --- | --- | --- |
| `/start` | hamma | Botni ishga tushirish |
| `/help` | hamma | Yordam |
| `/admin` | adminlar | Admin panel |
| `/bekor` | adminlar | Joriy amalni bekor qilish |
