"""
Scraper for Kyrgyzstan real estate portals: house.kg, lalafo.kg.

Extracts page text, photos, and structured property data
using BeautifulSoup for proper HTML parsing.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

KG_DOMAINS = {"house.kg", "www.house.kg", "lalafo.kg", "www.lalafo.kg"}


def is_kg_listing(url: str) -> bool:
    return urlparse(url).netloc.lower() in KG_DOMAINS


def scrape_listing(url: str) -> dict[str, Any]:
    """
    Scrape a KG real estate listing URL.
    Returns: page_text, photo_urls, and any pre-parsed fields.
    """
    domain = urlparse(url).netloc.lower()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return {"page_text": "", "photo_urls": []}

    if "house.kg" in domain:
        return _parse_house_kg(soup, url)
    elif "lalafo.kg" in domain:
        return _parse_lalafo_kg(soup, url)
    else:
        return _parse_generic(soup, url)


# ── house.kg ──────────────────────────────────────────────────────────────────

def _parse_house_kg(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    # Clean text
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    result["page_text"] = re.sub(r"\s{2,}", " ", text)[:12_000]

    # Photos — house.kg keeps them in .fotorama or data-src attributes
    photos: list[str] = []
    for img in soup.select("[data-src], [data-img], .fotorama img, .gallery img, .photos img"):
        src = img.get("data-src") or img.get("data-img") or img.get("src") or ""
        if src and _is_real_photo(src):
            photos.append(urljoin(url, src))
    # fallback
    if not photos:
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if src and _is_real_photo(src):
                photos.append(urljoin(url, src))
    result["photo_urls"] = list(dict.fromkeys(photos))[:10]

    # Pre-parse price
    price_el = (
        soup.select_one(".item-price")
        or soup.select_one(".price")
        or soup.find(class_=re.compile(r"price", re.I))
    )
    if price_el:
        result["price_raw"] = price_el.get_text(strip=True)

    # Title
    h1 = soup.find("h1")
    if h1:
        result["title"] = h1.get_text(strip=True)

    # Params table (rooms, area, floor, etc.)
    params: dict[str, str] = {}
    for row in soup.select("table tr, .params li, .characteristics li, dl dt"):
        cells = row.find_all(["td", "th", "dd"])
        if len(cells) >= 2:
            k = cells[0].get_text(strip=True)
            v = cells[1].get_text(strip=True)
            if k:
                params[k] = v
    result["params"] = params

    # Address/district
    addr = (
        soup.select_one(".address")
        or soup.find(class_=re.compile(r"address|district|location", re.I))
    )
    if addr:
        result["address_raw"] = addr.get_text(strip=True)

    return result


# ── lalafo.kg ─────────────────────────────────────────────────────────────────

def _parse_lalafo_kg(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    result["page_text"] = re.sub(r"\s{2,}", " ", text)[:12_000]

    photos: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
        if src and _is_real_photo(src):
            photos.append(urljoin(url, src))
    result["photo_urls"] = list(dict.fromkeys(photos))[:10]

    # lalafo stores price in .price or .AdCard-price
    price_el = soup.find(class_=re.compile(r"price", re.I))
    if price_el:
        result["price_raw"] = price_el.get_text(strip=True)

    h1 = soup.find("h1")
    if h1:
        result["title"] = h1.get_text(strip=True)

    return result


# ── generic fallback ──────────────────────────────────────────────────────────

def _parse_generic(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = re.sub(r"\s{2,}", " ", soup.get_text(" ", strip=True))

    photos = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if src and _is_real_photo(src):
            photos.append(urljoin(url, src))

    return {
        "page_text": text[:12_000],
        "photo_urls": list(dict.fromkeys(photos))[:10],
    }


def _is_real_photo(src: str) -> bool:
    src_lower = src.lower()
    if not any(ext in src_lower for ext in [".jpg", ".jpeg", ".png", ".webp"]):
        return False
    skip = ["icon", "logo", "1x1", "pixel", "tracking", "avatar", "sprite", "banner", "flag"]
    return not any(s in src_lower for s in skip)
