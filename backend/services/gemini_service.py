"""
Gemini Service — Google Gemini multimodal integration for ProphetAI.

This service accepts a real estate listing URL, fetches its content and
associated images, then submits everything to the Gemini API to extract
structured property data, identify red flags, and generate photo insights.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Maximum characters of page text to include in Gemini prompt (keeps token count manageable)
MAX_PAGE_TEXT_LENGTH = 8_000

# Maximum number of photos to attach inline (inline images are expensive on tokens)
MAX_INLINE_PHOTOS = 5

# Structured JSON schema the model must conform to
_LISTING_SCHEMA_PROMPT = """
You are ProphetAI, an expert real estate analyst.

Analyse the following real estate listing page content (and any photo URLs provided)
and return ONLY a valid JSON object that exactly matches this schema — no markdown fences,
no extra keys, no explanations:

{
  "address": "<full street address>",
  "city": "<city>",
  "state": "<2-letter state code>",
  "zip_code": "<ZIP>",
  "bedrooms": <integer or null>,
  "bathrooms": <number or null>,
  "square_feet": <integer or null>,
  "lot_size_sqft": <integer or null>,
  "year_built": <integer or null>,
  "listing_price": <number or null>,
  "property_type": "<Single Family | Condo | Townhouse | Multi-Family | Land | Other>",
  "description_summary": "<2–3 sentence summary>",
  "red_flags": [
    {
      "category": "<Structural | Water Damage | Electrical | Cosmetic | Legal | Pricing | Other>",
      "description": "<what was flagged>",
      "severity": "<Low | Medium | High>"
    }
  ],
  "photo_insights": [
    {
      "photo_url": "<url>",
      "room_type": "<Kitchen | Living Room | Bedroom | Bathroom | Exterior | Basement | Other>",
      "condition_score": <1–10 float>,
      "observations": ["<observation 1>", "<observation 2>"],
      "renovation_needed": <true | false>,
      "estimated_reno_cost_usd": <integer or null>
    }
  ],
  "neighbourhood_notes": "<brief neighbourhood observations if available>"
}

If a value cannot be determined from the content, use null.
"""


class GeminiService:
    """Wrapper around the Google Gemini 1.5 Pro multimodal API."""

    _MODEL = "gemini-1.5-pro-latest"
    _TIMEOUT = 30  # seconds for HTTP requests

    def __init__(self) -> None:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings.")

        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("google-generativeai package is not installed.") from exc

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(self._MODEL)

    # ──────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────

    def analyse_listing(self, listing_url: str) -> dict[str, Any]:
        """
        Fetch a listing URL, extract page text and photo URLs, then call
        Gemini to return structured analysis JSON.

        Returns a dictionary matching the schema defined in _LISTING_SCHEMA_PROMPT.
        """
        page_text, photo_urls = self._fetch_listing_page(listing_url)
        prompt_parts = self._build_prompt_parts(listing_url, page_text, photo_urls)
        response_text = self._call_gemini(prompt_parts)
        return self._parse_response(response_text)

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    def _fetch_listing_page(self, url: str) -> tuple[str, list[str]]:
        """Download the listing page and extract visible text + image URLs."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (compatible; ProphetAI/1.0; "
                    "+https://github.com/zeuscode-tech/ProphetAi)"
                )
            }
            resp = requests.get(url, headers=headers, timeout=self._TIMEOUT)
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as exc:
            logger.warning("Failed to fetch listing page %s: %s", url, exc)
            html = ""

        page_text = self._extract_text(html)
        photo_urls = self._extract_image_urls(html, url)
        return page_text, photo_urls

    @staticmethod
    def _extract_text(html: str) -> str:
        """Naively strip HTML tags to get readable page text."""
        # Remove scripts, styles, and HTML tags
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        return text[:MAX_PAGE_TEXT_LENGTH].strip()  # Limit to keep token count manageable

    @staticmethod
    def _extract_image_urls(html: str, base_url: str) -> list[str]:
        """Extract up to 10 <img src> URLs from the page."""
        base = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(base_url))
        raw_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
        resolved: list[str] = []
        for u in raw_urls:
            if u.startswith("http"):
                resolved.append(u)
            elif u.startswith("//"):
                resolved.append("https:" + u)
            elif u.startswith("/"):
                resolved.append(base + u)
        # Filter out tiny icons / tracking pixels heuristically
        filtered = [u for u in resolved if not any(x in u for x in ["icon", "logo", "pixel", "tracking", "1x1"])]
        return filtered[:10]

    def _build_prompt_parts(
        self,
        listing_url: str,
        page_text: str,
        photo_urls: list[str],
    ) -> list[Any]:
        """Construct the multimodal prompt for Gemini."""
        parts: list[Any] = [
            _LISTING_SCHEMA_PROMPT,
            f"\n\n--- LISTING URL ---\n{listing_url}\n",
            f"\n--- PAGE TEXT ---\n{page_text}\n",
        ]

        # Attempt to attach photos as inline image parts
        try:
            import google.generativeai as genai  # type: ignore[import]
            from google.generativeai.types import BlobDict  # type: ignore[import]

            for photo_url in photo_urls[:MAX_INLINE_PHOTOS]:
                try:
                    img_resp = requests.get(photo_url, timeout=10)
                    img_resp.raise_for_status()
                    content_type = img_resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
                    if content_type in ("image/jpeg", "image/png", "image/webp"):
                        parts.append({"mime_type": content_type, "data": img_resp.content})
                        parts.append(f"[Photo URL: {photo_url}]\n")
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Skipping image %s: %s", photo_url, exc)
        except ImportError:
            pass

        if photo_urls:
            parts.append(f"\n--- PHOTO URLS (for reference) ---\n" + "\n".join(photo_urls))

        return parts

    def _call_gemini(self, prompt_parts: list[Any]) -> str:
        """Send the prompt to the Gemini API and return the raw text response."""
        response = self._model.generate_content(prompt_parts)
        return response.text

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        """Parse Gemini's text output as JSON, stripping markdown fences if present."""
        # Strip ```json ... ``` or ``` ... ``` wrappers
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini response as JSON: %s\nRaw: %s", exc, text[:500])
            return {
                "address": "",
                "city": "",
                "state": "",
                "zip_code": "",
                "bedrooms": None,
                "bathrooms": None,
                "square_feet": None,
                "lot_size_sqft": None,
                "year_built": None,
                "listing_price": None,
                "red_flags": [],
                "photo_insights": [],
                "error": str(exc),
                "raw_response": text,
            }
