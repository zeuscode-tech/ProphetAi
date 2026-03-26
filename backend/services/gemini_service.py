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
        """
        # Весь этот код тоже должен быть с отступом в 8 пробелов
        scraped = scrape_listing(listing_url)
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
        # --- ОТЛАДКА: Посмотрим, сколько ссылок пришло из скрапера ---
        print(f"DEBUG: Scraper found {len(photo_urls)} photos total.")
        
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
            print(f"--- Processing {len(valid_photos)} photos for Gemini Vision... ---")
            
            for url in valid_photos:
                img_part = self._fetch_image_as_part(url)
                if img_part:
                    parts.append(img_part)
            
            parts.append("\n[System Instruction]: Анализируй изображения выше для оценки состояния ремонта.")

        return parts

    def _call_gemini(self, prompt_parts: list[Any]) -> str:
        try:
            # Добавляем принт, чтобы видеть прогресс в терминале
            print(f"--- Sending request to Gemini ({self._MODEL})... ---") 
            response = self._model.generate_content(prompt_parts)
            
            if not response.text:
                raise ValueError("Gemini returned empty response")
                
            print("--- Gemini responded successfully! ---")
            return response.text
        except Exception as e:
            print(f"!!! CRITICAL API ERROR: {str(e)}") # Это появится в черном окне
            logger.error(f"Gemini API Error: {str(e)}")
            # Вместо JSON возвращаем простую ошибку, чтобы parse_response это увидел
            raise e

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
