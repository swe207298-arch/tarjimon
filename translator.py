"""Tilni avtomatik aniqlash va 5 tilga tarjima qilish.

Google Translate'ning bepul (API kalitsiz) endpointidan foydalanadi.
"""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

import config

logger = logging.getLogger(__name__)

API_HOSTS = (
    "https://translate.googleapis.com",
    "https://clients5.google.com",
)

LANGUAGES: dict[str, dict[str, str]] = {
    "en": {"name": "Ingliz tili", "native": "English", "flag": "🇬🇧"},
    "ru": {"name": "Rus tili", "native": "Русский", "flag": "🇷🇺"},
    "ar": {"name": "Arab tili", "native": "العربية", "flag": "🇸🇦"},
    "zh-CN": {"name": "Xitoy tili", "native": "中文", "flag": "🇨🇳"},
    "uz": {"name": "O'zbek tili", "native": "O'zbekcha", "flag": "🇺🇿"},
}

_client: httpx.AsyncClient | None = None


class TranslationError(Exception):
    """Tarjima xizmatida yuz bergan xatolik."""


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=config.REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "uz,en;q=0.9,ru;q=0.8",
            },
        )
    return _client


async def close() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def normalize(code: str | None) -> str:
    """Turli xil til kodlarini yagona ko'rinishga keltiradi."""
    if not code:
        return "auto"
    code = code.strip()
    lowered = code.lower()
    if lowered.startswith("zh"):
        return "zh-CN"
    if lowered.startswith("en"):
        return "en"
    if lowered.startswith("ru"):
        return "ru"
    if lowered.startswith("ar"):
        return "ar"
    if lowered.startswith("uz"):
        return "uz"
    return code


def label(code: str | None) -> str:
    """Til uchun chiroyli nom: «🇺🇿 O'zbek tili»."""
    normalized = normalize(code)
    info = LANGUAGES.get(normalized)
    if info:
        return f"{info['flag']} {info['name']}"
    if normalized in ("auto", ""):
        return "🌐 Aniqlanmadi"
    return f"🌐 {normalized.upper()}"


def native_name(code: str | None) -> str:
    info = LANGUAGES.get(normalize(code))
    return info["native"] if info else ""


def flag(code: str | None) -> str:
    info = LANGUAGES.get(normalize(code))
    return info["flag"] if info else "🌐"


def split_text(text: str, limit: int = 3500) -> list[str]:
    """Uzun matnni tarjima uchun qismlarga bo'ladi (so'z chegarasida)."""
    text = (text or "").strip()
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind(". ", 0, limit)
        if cut < limit // 2:
            cut = remaining.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        parts.append(remaining)
    return parts or [""]


async def _request(text: str, target: str) -> tuple[str, str]:
    """Bitta bo'lakni tarjima qiladi. (tarjima, manba_til) qaytaradi."""
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target,
        "dt": "t",
        "dj": "1",
        "q": text,
    }
    last_error: Exception | None = None
    for host in API_HOSTS:
        try:
            response = await _get_client().get(f"{host}/translate_a/single", params=params)
            if response.status_code != 200:
                last_error = TranslationError(f"HTTP {response.status_code}")
                continue

            data = response.json()
            translated = ""
            source = "auto"

            if isinstance(data, dict):
                sentences = data.get("sentences") or []
                translated = "".join(
                    item.get("trans") or ""
                    for item in sentences
                    if isinstance(item, dict)
                ).strip()
                source = normalize(data.get("src"))
            elif isinstance(data, list):
                # Eski format: [[["tarjima", "asl", ...], ...], None, "en", ...]
                try:
                    translated = "".join(
                        part[0] for part in data[0] if part and part[0]
                    ).strip()
                except (TypeError, IndexError):
                    translated = ""
                if len(data) > 2:
                    source = normalize(data[2])

            if translated:
                return translated, source
            # Ba'zan faqat emoji/raqamlardan iborat matn uchun tarjima bo'sh keladi.
            return text, source
        except Exception as exc:  # noqa: BLE001 - har qanday tarmoq/format xatosi
            last_error = exc
            logger.warning("Tarjima serveri javob bermadi (%s): %s", host, exc)

    raise TranslationError("Tarjima xizmatiga ulanib bo'lmadi") from last_error


_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_ARABIC = re.compile(r"[\u0600-\u06FF]")
_CJK = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
_UZ_MARKERS = (
    "o'", "oʻ", "o‘", "g'", "gʻ", "g‘",
    " va ", " bu ", "uchun", "bilan", "salom", "rahmat",
    "yaxshi", "qanday", "nima", "kerak", "mumkin",
)


def _local_detect(text: str) -> str:
    """Internet xizmati ishlamasa, yozuv belgilariga qarab taxmin qiladi."""
    if _ARABIC.search(text):
        return "ar"
    if _CJK.search(text):
        return "zh-CN"
    if _CYRILLIC.search(text):
        return "ru"
    lowered = f" {text.lower()} "
    if any(marker in lowered for marker in _UZ_MARKERS):
        return "uz"
    return "en"


async def detect(text: str) -> str:
    """Matn tilini aniqlaydi. Xizmat ishlamasa — lokal taxmin."""
    sample = (text or "").strip()[:1000]
    if not sample:
        return "auto"
    try:
        _, source = await asyncio.wait_for(_request(sample, "en"), timeout=config.REQUEST_TIMEOUT)
        return source
    except Exception:  # noqa: BLE001 - aniqlash hech qachon bloklamasligi kerak
        logger.warning("Tilni aniqlashda xatolik, lokal taxmin ishlatiladi")
        return _local_detect(sample)


async def translate(text: str, target: str) -> tuple[str, str]:
    """Matnni tanlangan tilga tarjima qiladi. (tarjima, manba_til) qaytaradi."""
    target = normalize(target)
    if target not in LANGUAGES:
        raise TranslationError(f"Qo'llab-quvvatlanmaydigan til: {target}")

    source = "auto"
    translated_parts: list[str] = []
    for chunk in split_text(text):
        if not chunk:
            continue
        translated, chunk_source = await _request(chunk, target)
        if source == "auto" and chunk_source not in ("auto", ""):
            source = chunk_source
        translated_parts.append(translated)

    result = "\n".join(part for part in translated_parts if part).strip()
    if not result:
        raise TranslationError("Tarjima natijasi bo'sh")
    return result, source
