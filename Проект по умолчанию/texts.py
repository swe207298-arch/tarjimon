"""Botdagi barcha matnlar (o'zbek tilida, chiroyli HTML ko'rinishida)."""

from __future__ import annotations

WELCOME = (
    "👋 <b>Assalomu alaykum, {name}!</b>\n\n"
    "🌍 Men <b>5 tilli tarjimon</b> botiman.\n"
    "📝 Menga istalgan tilda matn yuboring — tilini o'zim aniqlayman.\n"
    "🌐 Keyin qaysi tilga tarjima qilishni o'zingiz tanlaysiz.\n\n"
    "<b>Mavjud tillar:</b>\n"
    "🇬🇧 Ingliz · 🇷🇺 Rus · 🇸🇦 Arab · 🇨🇳 Xitoy · 🇺🇿 O'zbek\n\n"
    "✍️ Boshlash uchun shunchaki matn yuboring 👇"
)

HELP = (
    "ℹ️ <b>Botdan foydalanish</b>\n\n"
    "1️⃣ Menga istalgan tilda matn yuboring.\n"
    "2️⃣ Bot tilni avtomatik aniqlaydi.\n"
    "3️⃣ Pastdagi chiroyli tugmalardan kerakli tilni tanlang.\n"
    "4️⃣ Tarjima bir zumda tayyor bo'ladi.\n\n"
    "🌐 <b>Mavjud tillar:</b>\n"
    "🇬🇧 Ingliz · 🇷🇺 Rus · 🇸🇦 Arab · 🇨🇳 Xitoy · 🇺🇿 O'zbek\n\n"
    "💡 <i>Maslahat:</i> uzun matnlarni ham bemalol yuboring — bot ularni "
    "qismlarga bo'lib tarjima qiladi."
)

DETECTED = (
    "🔍 <b>Til aniqlandi</b>\n\n"
    "🌐 Aniqlangan til: <b>{lang}</b>\n"
    "📄 Matn:\n<blockquote>{preview}</blockquote>\n\n"
    "👇 <b>Qaysi tilga tarjima qilamiz?</b>"
)

RESULT_HEADER = "✅ <b>Tarjima tayyor</b>\n\n{flag} <b>{native}</b>"
RESULT_FOOTER = "\n\n🔎 Asl til: {source}\n🔄 Boshqa tilni tanlang 👇"
LONG_NOTE = "\n\n<i>📄 Matn uzun — {count} qismda yuborildi.</i>"

SHORT_TEXT = "📝 Iltimos, tarjima uchun kamida 2 ta belgidan iborat matn yuboring."
NON_TEXT = "📝 Iltimos, tarjima uchun <b>matn</b> yuboring.\n\nRasm, video yoki stiker emas 🙂"
UNKNOWN_COMMAND = "🤔 Bunday buyruq mavjud emas.\n\nYordam uchun /help buyrug'ini yuboring."
ADMIN_ONLY = "⛔ Bu bo'lim faqat administratorlar uchun."
STALE_TEXT = "⌛️ Bu matn eskirgan. Iltimos, matnni qaytadan yuboring."
FOREIGN_BUTTON = "⛔ Bu tugma boshqa foydalanuvchiga tegishli."
TRANSLATE_ERROR = (
    "⚠️ Tarjima xizmatida vaqtincha xatolik yuz berdi.\n"
    "Birozdan so'ng qayta urinib ko'ring."
)

# ---------------------------------------------------------- majburiy kanal

SUBSCRIPTION_REQUIRED = (
    "🔒 <b>Botdan foydalanish uchun obuna bo'ling</b>\n\n"
    "Quyidagi kanallarga obuna bo'lgach, <b>«✅ Tekshirish»</b> tugmasini bosing."
)
SUBSCRIBED_OK = (
    "✅ <b>Obuna tasdiqlandi!</b>\n\n"
    "Endi botdan bemalol foydalanishingiz mumkin.\n"
    "Tarjima uchun matn yuboring 👇"
)
SUBSCRIBED_STILL = "❌ Siz hali barcha kanallarga obuna bo'lmadingiz."

# --------------------------------------------------------------- admin panel

ADMIN_MENU = (
    "🛠 <b>Admin panel</b>\n\n"
    "👥 Foydalanuvchilar: <b>{users}</b>\n"
    "📌 Majburiy kanallar: <b>{channels}</b>\n\n"
    "Kerakli bo'limni tanlang:"
)

BROADCAST_PROMPT = (
    "📢 <b>E'lon yuborish</b>\n\n"
    "Yubormoqchi bo'lgan xabaringizni yuboring — matn, rasm, video yoki "
    "boshqa kontent bo'lishi mumkin.\n\n"
    "Xabar barcha foydalanuvchilarga yuboriladi.\n"
    "<i>Bekor qilish uchun pastdagi tugmani bosing.</i>"
)

AD_PROMPT = (
    "📣 <b>Reklama yuborish</b>\n\n"
    "Avval reklama kontentini yuboring (matn yoki rasm).\n"
    "Keyingi qadamda unga havolali tugma qo'shasiz."
)

AD_BUTTON_PROMPT = (
    "🔗 <b>Reklama tugmasi</b>\n\n"
    "Tugmani quyidagi ko'rinishda yuboring:\n\n"
    "<code>Batafsil | https://t.me/kanalingiz</code>\n\n"
    "Tugmasiz yuborish uchun <code>/skip</code> deb yozing."
)

AD_BUTTON_INVALID = (
    "❌ Format noto'g'ri.\n\n"
    "Namuna: <code>Batafsil | https://t.me/kanalingiz</code>\n"
    "Yoki tugmasiz yuborish uchun <code>/skip</code> deb yozing."
)

BROADCAST_DONE = (
    "✅ <b>Yuborish yakunlandi</b>\n\n"
    "📬 Yuborildi: <b>{sent}</b>\n"
    "🚫 Yuborilmadi: <b>{failed}</b>\n"
    "👥 Jami: <b>{total}</b>"
)

ADMIN_CHANNELS_TITLE = (
    "📌 <b>Majburiy kanallar</b>\n\n"
    "Foydalanuvchi botdan foydalanishidan oldin ushbu kanallarga obuna bo'lishi shart.\n"
    "Kanallar soni: <b>{count}</b>\n"
)

ADMIN_CHANNELS_EMPTY = "\n<i>Hozircha majburiy kanal qo'shilmagan.</i>"
ADMIN_CHANNELS_HINT = (
    "\n<i>Kanal qo'shish uchun bot kanalda administrator bo'lishi kerak.</i>"
)

ADD_CHANNEL_PROMPT = (
    "➕ <b>Kanal qo'shish</b>\n\n"
    "Kanalning <code>@username</code> manzilini yuboring, havolasini tashlang "
    "yoki kanaldan bitta xabarni forward qiling.\n\n"
    "⚠️ <b>Muhim:</b> bot kanalda <b>administrator</b> bo'lishi va "
    "<b>«Taklif havolalari»</b> huquqiga ega bo'lishi kerak."
)

CHANNEL_NOT_FOUND = "❌ Kanal topilmadi. @username yoki havolani to'g'ri yuboring."
CHANNEL_NOT_CHANNEL = "❌ Bu kanal emas. Iltimos, kanal manzilini yuboring."
CHANNEL_CHECK_FAILED = "❌ Kanalni tekshirib bo'lmadi. Bot kanalga qo'shilganini tekshiring."
CHANNEL_BOT_NOT_ADMIN = (
    "❌ Bot <b>{title}</b> kanalida administrator emas.\n\n"
    "Avval botni kanalga administrator qilib qo'shing, so'ng qayta urinib ko'ring."
)
CHANNEL_NO_LINK = (
    "⚠️ Kanal uchun taklif havolasini olib bo'lmadi.\n\n"
    "Botga <b>«Taklif havolalari»</b> huquqini bering yoki kanalni "
    "<code>@username</code> bilan qayta qo'shing."
)
CHANNEL_ADDED = "✅ <b>{title}</b> majburiy kanallar ro'yxatiga qo'shildi."

ADMIN_STATS = (
    "📊 <b>Statistika</b>\n\n"
    "👥 Jami foydalanuvchilar: <b>{total}</b>\n"
    "🆕 Bugun qo'shildi: <b>{today}</b>\n"
    "🌐 Saqlangan tarjimalar: <b>{translations}</b>\n"
    "📌 Majburiy kanallar: <b>{channels}</b>"
)
