"""
Scraper for Kyrgyzstan real estate portals: house.kg, lalafo.kg.

Extracts page text, photos, and structured property data
using BeautifulSoup for proper HTML parsing.
"""

from __future__ import annotations

import json
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
    Returns: page_text, photo_urls, photo_count, and any pre-parsed fields.
    photo_count = total photos found in HTML/JSON (even if some fail to download).
    """
    domain = urlparse(url).netloc.lower()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return {"page_text": "", "photo_urls": [], "photo_count": 0}

    if "house.kg" in domain:
        return _parse_house_kg(soup, url)
    elif "lalafo.kg" in domain:
        return _parse_lalafo_kg(soup, url)
    else:
        return _parse_generic(soup, url)


def scrape_comparables(
    city: str,
    bedrooms: int | None,
    listing_price: float | None,
) -> list[dict[str, Any]]:
    """
    Scrape real comparable listings from house.kg search results.
    Returns up to 5 listings, or empty list on failure.
    """
    try:
        price = listing_price or 200_000
        price_min = int(price * 0.65)
        price_max = int(price * 1.35)
        beds = bedrooms or 3

        # Build search URL — house.kg accepts these query params
        city_lower = city.lower()
        if "бишкек" in city_lower or "bishkek" in city_lower:
            city_param = "city_id=1"
        elif "ош" in city_lower or "osh" in city_lower:
            city_param = "city_id=2"
        else:
            city_param = "city_id=1"

        search_url = (
            f"https://www.house.kg/buy?"
            f"{city_param}"
            f"&rooms_from={max(1, beds - 1)}"
            f"&rooms_to={beds + 1}"
            f"&price_usd_from={price_min}"
            f"&price_usd_to={price_max}"
        )

        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Try JSON data first (embedded in script tags)
        json_comps = _extract_comps_from_json(soup)
        if json_comps:
            return json_comps[:5]

        # Fallback: parse HTML listing cards
        comps: list[dict[str, Any]] = []
        # house.kg uses various card selectors — try all known patterns
        card_selectors = [
            ".listing-item",
            ".object-item",
            "[class*='ListingCard']",
            "[class*='listing-card']",
            "[class*='advert-card']",
            "[class*='PropertyCard']",
            "[data-id]",
        ]
        cards: list[Any] = []
        for sel in card_selectors:
            found = soup.select(sel)
            if found:
                cards = found
                break

        for card in cards[:10]:
            comp = _parse_comp_card(card)
            if comp:
                comps.append(comp)
            if len(comps) >= 5:
                break

        logger.info("Scraped %d real comparables from house.kg", len(comps))
        return comps

    except Exception as exc:
        logger.warning("scrape_comparables failed: %s", exc)
        return []


# ── house.kg ──────────────────────────────────────────────────────────────────

def _parse_house_kg(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    # ── Photos (before removing scripts/styles) ───────────────────────────────
    photos: list[str] = []

    # 1. house.kg fotorama: photos are in <a href> or <a data-full> inside .fotorama
    for a in soup.select(".fotorama a"):
        src = a.get("data-full") or a.get("href") or ""
        if src and _is_real_photo(src):
            photos.append(urljoin(url, src))

    # 2. Try to extract from embedded JSON (Next.js / Nuxt.js)
    if not photos:
        json_photos = _extract_photos_from_page_json(soup, url)
        photos.extend(json_photos)

    # 3. Standard HTML selectors
    if not photos:
        for img in soup.select("[data-src], [data-img], .gallery img, .photos img"):
            src = img.get("data-src") or img.get("data-img") or img.get("src") or ""
            if src and _is_real_photo(src):
                photos.append(urljoin(url, src))

    # 4. Generic img fallback (last resort)
    if not photos:
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-original") or ""
            if src and _is_real_photo(src):
                photos.append(urljoin(url, src))

    unique_photos = list(dict.fromkeys(photos))[:10]
    result["photo_urls"] = unique_photos
    result["photo_count"] = len(unique_photos)

    # ── Phone number ──────────────────────────────────────────────────────────
    result["phone_number"] = _extract_phone(soup)

    # ── Map coordinates ───────────────────────────────────────────────────────
    lat, lng = _extract_coords(soup)
    if lat and lng:
        result["map_lat"] = lat
        result["map_lng"] = lng

    # Clean text (after extracting structured data)
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    result["page_text"] = re.sub(r"\s{2,}", " ", text)[:12_000]

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

    # ── Params — house.kg uses .details-main .info-row with .label / .info ─────
    params: dict[str, str] = {}

    # Primary: house.kg specific structure
    for row in soup.select(".details-main .info-row, .object-info .info-row"):
        label_el = row.select_one(".label")
        info_el = row.select_one(".info")
        if label_el and info_el:
            k = label_el.get_text(strip=True)
            v = re.sub(r"\s{2,}", " ", info_el.get_text(" ", strip=True))
            if k and v:
                params[k] = v

    # Fallback: generic dl/table if primary found nothing
    if not params:
        for dl in soup.select("dl"):
            for k_el, v_el in zip(dl.find_all("dt"), dl.find_all("dd")):
                k = k_el.get_text(strip=True)
                v = v_el.get_text(strip=True)
                if k and v:
                    params[k] = v

        for row in soup.select("table tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                k = cells[0].get_text(strip=True)
                v = cells[1].get_text(strip=True)
                if k and v and k not in ("#", ""):
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
    unique_photos = list(dict.fromkeys(photos))[:10]
    result["photo_urls"] = unique_photos
    result["photo_count"] = len(unique_photos)

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
    unique_photos = list(dict.fromkeys(photos))[:10]

    return {
        "page_text": text[:12_000],
        "photo_urls": unique_photos,
        "photo_count": len(unique_photos),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_phone(soup: BeautifulSoup) -> str:
    """Extract phone number from house.kg listing page."""
    # 1. tel: links
    for a in soup.find_all("a", href=re.compile(r"^tel:")):
        phone = a["href"].replace("tel:", "").strip()
        if phone:
            return phone

    # 2. data-phone attributes
    el = soup.find(attrs={"data-phone": True})
    if el:
        return str(el["data-phone"]).strip()

    # 3. Look in page text for KG phone pattern (+996 or 0 followed by 9 digits)
    text = soup.get_text(" ")
    match = re.search(r'(\+996[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3}|\b0\d{9}\b)', text)
    if match:
        return match.group(1).strip()

    # 4. JSON data
    for script in soup.find_all("script"):
        t = script.string or ""
        if "phone" not in t.lower():
            continue
        m = re.search(r'"phone[^"]*"\s*:\s*"([+\d\s\-]{7,20})"', t, re.I)
        if m:
            return m.group(1).strip()

    return ""


def _extract_coords(soup: BeautifulSoup) -> tuple[float | None, float | None]:
    """Extract latitude/longitude from house.kg listing page."""
    # 1. house.kg map div: <div id="map2gis" data-lat="..." data-lon="...">
    el = soup.find(id="map2gis")
    if el:
        try:
            lat = float(el.get("data-lat", 0))
            lon = float(el.get("data-lon", 0))
            if lat and lon:
                return lat, lon
        except (ValueError, TypeError):
            pass

    # 2. Any element with data-lat + data-lon or data-lat + data-lng
    for attr_lng in ("data-lon", "data-lng"):
        el = soup.find(attrs={"data-lat": True, attr_lng: True})
        if el:
            try:
                lat = float(el["data-lat"])
                lng = float(el[attr_lng])
                if 39 < lat < 44 and 69 < lng < 81:
                    return lat, lng
            except (ValueError, TypeError):
                pass

    # 3. Inline script vars: var lat = 42.87; var lon = 74.59;
    for script in soup.find_all("script"):
        t = script.string or ""
        if not t or "lat" not in t.lower():
            continue
        lat_m = re.search(r'\blat\b\s*[=:]\s*(4[0-4]\.\d+)', t)
        lon_m = re.search(r'\blo[ng]\b\s*[=:]\s*(7[0-9]\.\d+)', t)
        if lat_m and lon_m:
            try:
                return float(lat_m.group(1)), float(lon_m.group(1))
            except (ValueError, TypeError):
                pass

    # 4. Meta geo tags
    meta_lat = soup.find("meta", attrs={"name": "geo.position"})
    if meta_lat:
        content = meta_lat.get("content", "")
        parts = content.split(";")
        if len(parts) == 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except (ValueError, TypeError):
                pass

    return None, None


def _is_real_photo(src: str) -> bool:
    src_lower = src.lower()
    # Accept explicit image extensions OR common CDN URL patterns (no extension in path)
    has_ext = any(ext in src_lower for ext in [".jpg", ".jpeg", ".png", ".webp"])
    is_cdn = any(
        cdn in src_lower
        for cdn in ["img.house.kg", "cdn.house.kg", "images.house.kg",
                    "cdn.lalafo.kg", "i.lalafo.kg"]
    )
    if not has_ext and not is_cdn:
        return False
    skip = ["icon", "logo", "1x1", "pixel", "tracking", "avatar", "sprite", "banner", "flag"]
    return not any(s in src_lower for s in skip)


def _extract_photos_from_page_json(soup: BeautifulSoup, base_url: str) -> list[str]:
    """
    Try to extract photo URLs from embedded page JSON (Next.js __NEXT_DATA__,
    Nuxt __NUXT_DATA__, or any script block containing image URLs).
    """
    photos: list[str] = []

    # Pattern 1: Next.js __NEXT_DATA__
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data and next_data.string:
        photos.extend(_walk_json_for_photos(next_data.string, base_url))
        if photos:
            return photos

    # Pattern 2: Nuxt — window.__NUXT__ or similar
    for script in soup.find_all("script"):
        text = script.string or ""
        if not text:
            continue
        # Look for JSON blocks that contain photo/image arrays
        if "photo" not in text.lower() and "image" not in text.lower():
            continue
        # Extract JSON-like structures
        json_matches = re.findall(r'\{[^{}]{20,}\}', text)
        for match in json_matches[:30]:
            photos.extend(_walk_json_for_photos(match, base_url))
        if photos:
            return list(dict.fromkeys(photos))[:10]

    return photos


def _walk_json_for_photos(json_str: str, base_url: str) -> list[str]:
    """Recursively walk a JSON structure looking for image URL values."""
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return []

    photos: list[str] = []
    _collect_photo_urls(data, photos)
    return [urljoin(base_url, u) for u in photos if _is_real_photo(u)]


def _collect_photo_urls(obj: Any, results: list[str]) -> None:
    """DFS through any JSON structure to collect image URLs."""
    if isinstance(obj, str):
        if _is_real_photo(obj) and obj.startswith("http"):
            results.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("url", "src", "photo", "image", "img", "thumbnail", "original"):
                if isinstance(v, str) and _is_real_photo(v):
                    results.append(v)
            else:
                _collect_photo_urls(v, results)
    elif isinstance(obj, list):
        for item in obj:
            _collect_photo_urls(item, results)


def _extract_comps_from_json(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Try to extract comparable listing data from embedded JSON on search page."""
    for script in soup.find_all("script"):
        text = script.string or ""
        if not text or "price" not in text.lower():
            continue
        try:
            # Look for JSON arrays that might be listing data
            matches = re.findall(r'\[(\{[^[\]]{50,}\}(?:,\{[^[\]]{50,}\})*)\]', text)
            for match in matches[:5]:
                try:
                    items = json.loads(f"[{match}]")
                    comps = [_normalize_comp_from_json(item) for item in items if isinstance(item, dict)]
                    comps = [c for c in comps if c is not None]
                    if comps:
                        return comps[:5]
                except Exception:
                    continue
        except Exception:
            continue
    return []


def _normalize_comp_from_json(item: dict[str, Any]) -> dict[str, Any] | None:
    """Try to extract comparable sale fields from a JSON object."""
    price = (
        item.get("price_usd") or item.get("price") or
        item.get("priceUsd") or item.get("cost")
    )
    address = (
        item.get("address") or item.get("title") or
        item.get("location") or item.get("district")
    )
    if not price or not address:
        return None
    try:
        price_val = float(str(price).replace(",", "").replace(" ", ""))
    except (ValueError, TypeError):
        return None
    return {
        "address": str(address)[:80],
        "sale_price": price_val,
        "bedrooms": item.get("rooms") or item.get("bedrooms"),
        "square_feet": item.get("area") or item.get("square_feet"),
        "days_ago": item.get("days_ago", 0),
    }


def _parse_comp_card(card: Any) -> dict[str, Any] | None:
    """Parse a house.kg search result card element into a comparable dict."""
    try:
        text = card.get_text(" ", strip=True)

        # Extract price — look for USD amounts like $250,000 or 250 000 $
        price_match = re.search(
            r'[\$]?\s*(\d[\d\s,\.]{2,10})\s*(?:USD|\$|сом)?',
            text
        )
        if not price_match:
            return None
        price_str = re.sub(r'[\s,]', '', price_match.group(1).replace('.', ''))
        try:
            price = float(price_str)
        except ValueError:
            return None
        # Sanity check — prices in KGS need conversion
        if price > 100_000_000:
            price = price / 89  # KGS → USD
        if price < 5_000 or price > 5_000_000:
            return None

        # Extract address/title
        title_el = card.select_one("h2, h3, .title, .address, [class*='title'], [class*='address']")
        address = title_el.get_text(strip=True) if title_el else text[:60]

        # Extract rooms
        rooms_match = re.search(r'(\d+)\s*(?:комн|спал|бдр|rooms?)', text, re.I)
        bedrooms = int(rooms_match.group(1)) if rooms_match else None

        # Extract area
        area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:м²|кв\.?м?|sqm)', text, re.I)
        square_feet = float(area_match.group(1)) if area_match else None

        return {
            "address": address[:80],
            "sale_price": price,
            "bedrooms": bedrooms,
            "square_feet": square_feet,
            "days_ago": 0,
        }
    except Exception:
        return None
