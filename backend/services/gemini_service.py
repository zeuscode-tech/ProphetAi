"""
Gemini Service — Google Gemini multimodal integration for ProphetAI.

Accepts a real estate listing URL (incl. house.kg / lalafo.kg),
scrapes it with BeautifulSoup, then calls Gemini 1.5 Pro to extract
structured property data, red flags, and photo insights.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.conf import settings

from services.kg_scraper import is_kg_listing, scrape_listing

logger = logging.getLogger(__name__)

MAX_INLINE_PHOTOS = 5

_LISTING_SCHEMA_PROMPT = """
Act as a Professional Real Estate Investment Analyst specializing in the CIS market (Kyrgyzstan/Kazakhstan).
Your task is to analyze property descriptions and images to provide a structured financial and technical assessment.

Return ONLY a valid JSON object. No markdown, no explanations outside the JSON.

{
  "address": "<full street address>",
  "city": "<city, e.g. Бишкек / Ош>",
  "state": "<region, e.g. Чуйская / Ошская>",
  "zip_code": "<postal code or null>",
  "bedrooms": <integer or null>,
  "bathrooms": <number or null>,
  "square_feet": <area in sqm as integer or null>,
  "lot_size_sqft": <land area in sqm or null>,
  "year_built": <integer or null>,
  "listing_price": <price in USD — convert from KGS if needed: 1 USD ≈ 89 KGS>,
  "property_type": "<Квартира | Дом | Коттедж | Участок | Коммерческая | Другое>",
  "condition": "<Новостройка | Евроремонт | Хорошее | Среднее | Требует ремонта>",
  "description_summary": "<краткое описание 2-3 предложения на РУССКОМ языке>",
  "neighbourhood_notes": "<район, инфраструктура, транспорт — на РУССКОМ языке>",
  "valuation": {
    "estimated_price": <fair market price in USD based on district + condition, NOT seller price>,
    "confidence_score": <0.0–1.0>,
    "price_per_sqm": <USD per sqm>,
    "market_position": "<undervalued | fair | overvalued>"
  },
  "condition_analysis": {
    "repair_quality": <1–10>,
    "style": "<modern | classic | soviet | unfinished>",
    "features": ["<key feature from photos>"],
    "red_flags": [
      {
        "issue": "<краткое название проблемы на РУССКОМ>",
        "severity": "<high | medium | low>",
        "description": "<объяснение риска на РУССКОМ языке>"
      }
    ]
  },
  "investment_potential": {
    "score": <1–100>,
    "rental_yield_est": "<percentage string, e.g. '7.5%'>",
    "liquidity": "<high | medium | low>"
  },
  "photo_insights": [
    {
      "room_type": "<название комнаты на РУССКОМ: Кухня | Гостиная | Спальня | Ванная | Фасад | Двор | Другое>",
      "condition_score": <оценка состояния 1.0–10.0 на основе фото>,
      "observations": ["<конкретное наблюдение 1 на русском>", "<наблюдение 2>"],
      "renovation_needed": <true если нужен ремонт, иначе false>,
      "estimated_reno_cost_usd": <примерная стоимость ремонта в USD или null>
    }
  ]
}

ПРАВИЛА ДЛЯ photo_insights:
- Анализируй только предоставленные фотографии. Для каждого уникального типа комнаты — ОДНА запись.
- НЕ дублируй room_type. Если 3 спальни — сделай одну запись "Спальня" с усреднённой оценкой.
- Если фото нет или тип комнаты неизвестен — используй "Общий вид".
- observations должны быть конкретными (пример: "Свежая плитка", "Старая сантехника") — не общими фразами.
- Минимум 2 observations на каждую запись.

STRICT RULES:
1. If year_built is 2025 or later AND the listing condition is NOT "Новостройка"/"новостройка" AND the listing does NOT explicitly say it is completed/сдан — then add a high-severity red_flag: "Under Construction / Data Error". If condition IS "Новостройка" or listing says it is a new development, do NOT add this flag just for the year alone.
2. If description says "Luxury" / "Евроремонт" but photos show old furniture or poor finishes, add High severity red_flag: "Описание не соответствует фото". Only add this flag if you actually see the photos — do not add it based on text alone.
3. estimated_price must be calculated from district benchmarks + condition multiplier, not just the seller's price.
4. listing_price always in USD (convert KGS → USD at 1:89).
5. square_feet is sqm (post-Soviet standard), not square feet.
6. If a value cannot be determined, use null.
7. IMPORTANT: Do NOT add a "no photos" red flag if the metadata says the listing has photos. Only flag absent photos if LISTING_PHOTO_COUNT = 0.
"""

class GeminiService:
    # Эти переменные внутри класса
    _MODEL = 'gemini-2.5-flash'
    _TIMEOUT = 30

    def __init__(self) -> None:
        # Внутри метода еще +4 пробела (итого 8)
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self._MODEL)

    def analyse_listing(self, listing_url: str) -> dict[str, Any]:
        """
        Scrape listing → build multimodal prompt → call Gemini → return structured dict.
        Scraped raw data is stored on self.last_scraped for the caller to access.
        """
        scraped = scrape_listing(listing_url)
        self.last_scraped = scraped  # expose to caller (views.py)

        page_text = scraped.get("page_text", "")
        photo_urls = scraped.get("photo_urls", [])

        extra_context = self._build_extra_context(scraped)
        prompt_parts = self._build_prompt_parts(listing_url, page_text, photo_urls, extra_context)

        response_text = self._call_gemini(prompt_parts)
        return self._parse_response(response_text)

    # Не забудь сдвинуть остальные методы (_call_gemini, _parse_response и т.д.) тоже!

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_extra_context(scraped: dict[str, Any]) -> str:
        parts = []
        if scraped.get("title"):
            parts.append(f"Title: {scraped['title']}")
        if scraped.get("price_raw"):
            parts.append(f"Price (raw): {scraped['price_raw']}")
        if scraped.get("address_raw"):
            parts.append(f"Address (raw): {scraped['address_raw']}")
        if scraped.get("params"):
            params_str = ", ".join(f"{k}: {v}" for k, v in scraped["params"].items())
            parts.append(f"Params: {params_str}")
        # Tell Gemini how many photos the listing actually has on the website.
        # This prevents it from generating a "no photos" flag when photos exist
        # but couldn't be downloaded for analysis.
        photo_count = scraped.get("photo_count", len(scraped.get("photo_urls", [])))
        parts.append(f"LISTING_PHOTO_COUNT: {photo_count}")
        return "\n".join(parts)

    def _fetch_image_as_part(self, url: str) -> dict[str, Any] | None:
        """Скачивает изображение и готовит его для мультимодального запроса."""
        import requests
        import base64
        try:
            # House.kg может блокировать пустые User-Agent
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                return {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(resp.content).decode("utf-8")
                    }
                }
        except Exception as e:
            logger.warning(f"Не удалось загрузить фото для анализа: {url}. Ошибка: {e}")
        return None

    def _build_prompt_parts(
        self,
        listing_url: str,
        page_text: str,
        photo_urls: list[str],
        extra_context: str,
    ) -> list[Any]:
        parts: list[Any] = [
            _LISTING_SCHEMA_PROMPT,
            f"\n\n--- LISTING URL ---\n{listing_url}\n",
        ]
        
        if extra_context:
            parts.append(f"\n--- PRE-PARSED DATA ---\n{extra_context}\n")
        
        parts.append(f"\n--- PAGE TEXT ---\n{page_text}\n")

        # Если ссылок много, мы берем только MAX_INLINE_PHOTOS (например, 5 или 10)
        if photo_urls:
            # Важно: берем срез [:MAX_INLINE_PHOTOS]
            valid_photos = photo_urls[:MAX_INLINE_PHOTOS]
            logger.debug("Processing %d photos for Gemini Vision.", len(valid_photos))
            
            for url in valid_photos:
                img_part = self._fetch_image_as_part(url)
                if img_part:
                    parts.append(img_part)
            
            parts.append("\n[System Instruction]: Анализируй изображения выше для оценки состояния ремонта.")

        return parts

    def _call_gemini(self, prompt_parts: list[Any]) -> str:
        try:
            logger.info("Sending request to Gemini (%s)...", self._MODEL)
            response = self._model.generate_content(prompt_parts)

            if not response.text:
                raise ValueError("Gemini returned empty response")

            logger.info("Gemini responded successfully.")
            return response.text
        except Exception as e:
            logger.error("Gemini API Error: %s", str(e))
            raise e

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini JSON: %s\nRaw: %s", exc, text[:500])
            return {
                "address": "", "city": "", "state": "", "zip_code": "",
                "bedrooms": None, "bathrooms": None, "square_feet": None,
                "lot_size_sqft": None, "year_built": None, "listing_price": None,
                "red_flags": [], "photo_insights": [],
                "error": str(exc), "raw_response": text,
            }

        # ── Normalize photo_captions labels ───────────────────────────────────
        _UNKNOWN_LABELS = {"", "unknown", "other", "unknown room", "none", "null"}
        for caption in data.get("photo_captions", []):
            label = (caption.get("label") or "").strip()
            if label.lower() in _UNKNOWN_LABELS:
                caption["label"] = "Общий вид"

        # ── Normalize red_flags issues ────────────────────────────────────────
        for flag in data.get("condition_analysis", {}).get("red_flags", []):
            issue = (flag.get("issue") or "").strip()
            if not issue or issue.lower() in {"other", "unknown", "none"}:
                flag["issue"] = "Анализ риска"
            # Ensure category field exists for frontend
            if not flag.get("category"):
                flag["category"] = flag["issue"]

        return data
