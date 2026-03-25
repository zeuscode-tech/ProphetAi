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
You are ProphetAI, an expert real estate analyst specialising in the Kyrgyzstan property market
(but also capable of analysing any international listing).

Analyse the real estate listing content below and return ONLY a valid JSON object that exactly
matches this schema — no markdown fences, no extra keys, no explanations:

{
  "address": "<full street address>",
  "city": "<city name, e.g. Бишкек / Ош / Чуй>",
  "state": "<region or oblast, e.g. Чуйская / Ошская>",
  "zip_code": "<ZIP or postal code if available, else null>",
  "bedrooms": <integer or null>,
  "bathrooms": <number or null>,
  "square_feet": <total area in sqm as integer, or null>,
  "lot_size_sqft": <land area in sqm if available, else null>,
  "year_built": <integer or null>,
  "listing_price": <price as a number in USD. If price is in KGS, convert: 1 USD ≈ 89 KGS>,
  "currency": "<USD | KGS | RUB>",
  "floor": <floor number as integer or null>,
  "total_floors": <total floors in building as integer or null>,
  "property_type": "<Квартира | Дом | Коттедж | Участок | Коммерческая | Другое>",
  "condition": "<Новостройка | Евроремонт | Хорошее | Среднее | Требует ремонта>",
  "description_summary": "<2–3 sentence summary in Russian>",
  "red_flags": [
    {
      "category": "<Конструктив | Влажность | Электрика | Косметика | Юридическое | Цена | Другое>",
      "description": "<что именно вызывает опасение>",
      "severity": "<Low | Medium | High>"
    }
  ],
  "photo_insights": [
    {
      "photo_url": "<url>",
      "room_type": "<Кухня | Гостиная | Спальня | Санузел | Фасад | Подвал | Двор | Другое>",
      "condition_score": <1–10 float>,
      "observations": ["<наблюдение 1>", "<наблюдение 2>"],
      "renovation_needed": <true | false>,
      "estimated_reno_cost_usd": <integer or null>
    }
  ],
  "neighbourhood_notes": "<краткое описание района, инфраструктуры, транспортной доступности>"
}

Important rules:
- listing_price must always be in USD (convert if needed, 1 USD ≈ 89 KGS as of 2024)
- square_feet field contains area in SQM (standard in KG/post-Soviet market), not sq.ft.
- If a value cannot be determined, use null.
- For Bishkek listings: note the district (мкр Аламедин, Асанбай, Джал, Восток-5, Южные Магистрали, etc.)
"""


class GeminiService:
    """Wrapper around the Google Gemini 1.5 Pro multimodal API."""

    _MODEL = "gemini-1.5-flash"
    _TIMEOUT = 30

    def __init__(self) -> None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ImportError("google-generativeai package is not installed.") from exc

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self._MODEL)

    def analyse_listing(self, listing_url: str) -> dict[str, Any]:
        """
        Scrape listing → build multimodal prompt → call Gemini → return structured dict.
        """
        scraped = scrape_listing(listing_url)
        page_text = scraped.get("page_text", "")
        photo_urls = scraped.get("photo_urls", [])

        # Enrich prompt with pre-parsed fields if available
        extra_context = self._build_extra_context(scraped)

        prompt_parts = self._build_prompt_parts(listing_url, page_text, photo_urls, extra_context)
        response_text = self._call_gemini(prompt_parts)
        return self._parse_response(response_text)

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
        return "\n".join(parts)

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

        if photo_urls:
            parts.append("\n--- PHOTO URLS (describe what you can infer from these URLs and filenames) ---\n" + "\n".join(photo_urls))

        return parts

    def _call_gemini(self, prompt_parts: list[Any]) -> str:
        response = self._model.generate_content(prompt_parts)
        return response.text

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini JSON: %s\nRaw: %s", exc, text[:500])
            return {
                "address": "", "city": "", "state": "", "zip_code": "",
                "bedrooms": None, "bathrooms": None, "square_feet": None,
                "lot_size_sqft": None, "year_built": None, "listing_price": None,
                "red_flags": [], "photo_insights": [],
                "error": str(exc), "raw_response": text,
            }
