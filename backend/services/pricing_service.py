"""
Pricing Service — fair-market value estimation for ProphetAI (Kyrgyzstan market).

Uses a heuristic model calibrated to KG real estate prices (in USD).
If a trained XGBoost model artifact is found, it takes priority.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_artifacts", "xgb_model.pkl")

# ── KG market price benchmarks (USD per sqm of building area) ────────────────
# Apartment prices — base for heuristic
_CITY_PRICE_PER_SQM: dict[str, float] = {
    "бишкек": 900,
    "bishkek": 900,
    "bishkek центр": 1300,
    "аламедин": 750,
    "асанбай": 820,
    "джал": 870,
    "восток-5": 780,
    "южные магистрали": 810,
    "ак-орго": 760,
    "кара-жыгач": 700,
    "ош": 500,
    "osh": 500,
    "жалал-абад": 380,
    "jalal-abad": 380,
    "каракол": 350,
    "токмок": 320,
    "кант": 310,
    "чуй": 600,
    "чуйская": 600,
}
_DEFAULT_PRICE_PER_SQM = 700

# ── Land price benchmarks (USD per sqm of land) ───────────────────────────────
# Source: house.kg land listings 2024. 1 сотка = 100 sqm.
# Central Bishkek (ул. Карла Маркса, Московская, Манаса, Байтик Баатыра): ~$300-500/sqm
# Average Bishkek residential (Аламедин, Джал, Асанбай): ~$100-250/sqm
# Bishkek suburbs / outskirts: ~$50-100/sqm
_CITY_LAND_PRICE_PER_SQM: dict[str, float] = {
    "бишкек": 180,       # Average residential Bishkek
    "bishkek": 180,
    "ош": 80,
    "osh": 80,
    "жалал-абад": 45,
    "jalal-abad": 45,
    "каракол": 40,
    "токмок": 30,
    "чуйская": 60,
    "чуй": 60,
}
_DEFAULT_LAND_PRICE_PER_SQM = 50

# Central street keywords → premium land (+80% over city average)
_CENTRAL_STREETS = [
    "карла маркса", "karl marks", "московская", "манаса", "manas",
    "чуй", "chui", "байтик баатыра", "боконбаева", "токтогула",
    "филармония", "центр", "center",
]

# ── Bishkek housing series (советские серии) ──────────────────────────────────
# Source: house.kg analytics + local broker data 2023-2024
_SERIES_MULTIPLIERS: dict[str, float] = {
    "104":        0.78,   # Хрущёвка 1960-х, маленькие комнаты, низкие потолки
    "серия 104":  0.78,
    "105":        0.85,   # Улучшенная планировка, чуть больше площадь
    "серия 105":  0.85,
    "106":        0.92,   # Крупнопанельная, 1970-80е, приемлемое состояние
    "серия 106":  0.92,
    "улан":       0.88,
    "кмс":        0.90,
    "гипс":       0.83,
    "байтик":     0.95,
    "инд":        1.15,   # Индивидуальный проект — премиум
    "индивидуальный": 1.15,
    "монолит":    1.20,
    "кирпич":     1.10,
    "новостройка": 1.18,
}

# ── Condition multipliers ─────────────────────────────────────────────────────
_CONDITION_MULTIPLIERS: dict[str, float] = {
    "новостройка":     1.20,
    "евроремонт":      1.15,
    "хорошее":         1.00,
    "среднее":         0.87,
    "требует ремонта": 0.70,
    "modern":          1.15,
    "classic":         0.95,
    "soviet":          0.82,
    "unfinished":      0.65,
}

# ── Investment score condition weights (1-10 → factor) ───────────────────────
_CONDITION_SCORE_FACTOR: dict[str, float] = {
    "новостройка": 1.0, "евроремонт": 0.95, "хорошее": 0.85,
    "среднее": 0.70, "требует ремонта": 0.50,
    "modern": 0.95, "classic": 0.80, "soviet": 0.65, "unfinished": 0.40,
}


def calculate_investment_score(
    market_price: float,
    fair_price: float,
    condition: str,
) -> float:
    """
    Calculate investment attractiveness score (1–100).

    Args:
        market_price: Seller's asking price in USD.
        fair_price:   AI-estimated fair market value in USD.
        condition:    Property condition string (matches _CONDITION_SCORE_FACTOR keys).

    Returns:
        Score from 1.0 to 100.0. Higher = better investment.
    """
    if fair_price <= 0:
        return 20.0

    # 1. Price delta component (0–60 points).
    #    Uses listing price vs fair price. Capped so that even extreme overpricing
    #    doesn't drop below 0 (the property itself still has value).
    delta_ratio = (fair_price - market_price) / fair_price  # negative = overpriced
    # Map delta_ratio [-1..+1] → price_component [0..60]
    price_component = 30.0 + delta_ratio * 30.0
    price_component = max(0.0, min(60.0, price_component))

    # 2. Condition component (0–30 points)
    cond_key = condition.lower().strip() if condition else ""
    cond_factor = _CONDITION_SCORE_FACTOR.get(cond_key, 0.75)
    if cond_factor == 0.75:  # partial match
        for key, val in _CONDITION_SCORE_FACTOR.items():
            if key in cond_key:
                cond_factor = val
                break
    condition_component = cond_factor * 30.0  # max 30 points

    # 3. Liquidity component (0–10 points): affordable properties sell faster in KG
    if fair_price < 50_000:
        liquidity_component = 10.0
    elif fair_price < 120_000:
        liquidity_component = 7.0
    elif fair_price < 300_000:
        liquidity_component = 4.0
    else:
        liquidity_component = 1.0

    raw = price_component + condition_component + liquidity_component
    # Floor of 20: even the worst overpriced property isn't a 1/100
    return round(max(20.0, min(98.0, raw)), 2)


class PricingService:

    def __init__(self) -> None:
        self._model = self._load_model()

    def predict(
        self,
        bedrooms: int | None,
        bathrooms: float | None,
        square_feet: int | None,
        lot_size_sqft: int | None = None,
        year_built: int | None = None,
        city: str = "",
        state: str = "",
        zip_code: str = "",
        condition: str = "",
        series: str = "",
        listing_price: float | None = None,
        listing_url: str = "",
        property_type: str = "",
        address: str = "",
        gemini_estimated_price: float | None = None,
    ) -> dict[str, Any]:
        fair_price = self._estimate_price(
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
            lot_size_sqft=lot_size_sqft,
            year_built=year_built,
            city=city,
            condition=condition,
            series=series,
            property_type=property_type,
            address=address,
        )

        # Blend with Gemini's valuation when available.
        # Gemini analyzes photos + text context; heuristic uses benchmarks.
        # Weighted blend: 40% Gemini + 60% heuristic (heuristic anchors to market data).
        if gemini_estimated_price and gemini_estimated_price > 0:
            fair_price = round(0.60 * fair_price + 0.40 * gemini_estimated_price, 2)
            logger.info(
                "Blended price: heuristic=%.0f, gemini=%.0f → final=%.0f",
                fair_price / 0.60, gemini_estimated_price, fair_price,
            )

        market_price = listing_price or fair_price
        inv_score = calculate_investment_score(market_price, fair_price, condition)

        price_delta_pct = 0.0
        if market_price and market_price > 0:
            price_delta_pct = round((fair_price - market_price) / market_price * 100, 2)

        return {
            "estimated_price": round(fair_price, 2),
            "investment_score": inv_score,
            "rental_yield_pct": round(self._rental_yield(fair_price, city), 2),
            "appreciation_trend_pct": round(self._appreciation(city, state), 2),
            "price_delta_pct": price_delta_pct,
            "comparable_sales": self._fetch_comparables(city, bedrooms, listing_price),
            "confidence_interval": {
                "low": round(fair_price * 0.88, 2),
                "high": round(fair_price * 1.12, 2),
            },
        }

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _load_model() -> Any | None:
        if not os.path.exists(_MODEL_PATH):
            logger.info("No trained model at %s; using KG heuristic.", _MODEL_PATH)
            return None
        try:
            import pickle
            with open(_MODEL_PATH, "rb") as f:
                return pickle.load(f)
        except Exception as exc:
            logger.warning("Failed to load model: %s", exc)
            return None

    def _estimate_price(
        self,
        bedrooms: int | None,
        bathrooms: float | None,
        square_feet: int | None,
        lot_size_sqft: int | None,
        year_built: int | None,
        city: str,
        condition: str,
        series: str = "",
        property_type: str = "",
        address: str = "",
    ) -> float:
        if self._model is not None:
            return self._predict_with_model(bedrooms, bathrooms, square_feet, lot_size_sqft, year_built)
        return self._heuristic_kg(
            bedrooms, square_feet, lot_size_sqft, year_built,
            city, condition, series, property_type, address,
        )

    def _predict_with_model(self, bedrooms, bathrooms, square_feet, lot_size_sqft, year_built) -> float:
        features = np.array([[
            bedrooms or 2,
            bathrooms or 1.0,
            square_feet or 50,
            lot_size_sqft or 0,
            year_built or 2000,
        ]], dtype=np.float32)
        return float(self._model.predict(features)[0])

    @staticmethod
    def _heuristic_kg(
        bedrooms: int | None,
        square_feet: int | None,
        lot_size_sqft: int | None,
        year_built: int | None,
        city: str,
        condition: str,
        series: str = "",
        property_type: str = "",
        address: str = "",
    ) -> float:
        sqm = square_feet or (bedrooms or 2) * 25 + 20
        city_key = city.lower().strip()
        addr_key = address.lower()

        # ── Building price per sqm ────────────────────────────────────────────
        price_per_sqm = _DEFAULT_PRICE_PER_SQM
        for key, val in _CITY_PRICE_PER_SQM.items():
            if key in city_key or city_key in key:
                price_per_sqm = val
                break

        # ── Property type multiplier ──────────────────────────────────────────
        # Houses / cottages command 25–40% premium over apartments per sqm
        # because they include individual infrastructure (roof, foundation, etc.)
        prop_type_key = property_type.lower()
        is_house = (
            any(t in prop_type_key for t in ("дом", "коттедж", "house", "cottage", "таун"))
            or (lot_size_sqft is not None and lot_size_sqft >= 200)  # infer from land area
        )
        if is_house:
            price_per_sqm *= 1.30

        base = sqm * price_per_sqm

        # ── Condition adjustment ──────────────────────────────────────────────
        cond_key = condition.lower().strip() if condition else ""
        for key, mult in _CONDITION_MULTIPLIERS.items():
            if key in cond_key:
                base *= mult
                break

        # ── Housing series adjustment (apartments only) ───────────────────────
        if not is_house:
            series_key = series.lower().strip() if series else ""
            if not series_key:
                combined = f"{cond_key} {city_key}"
                for key in _SERIES_MULTIPLIERS:
                    if key in combined:
                        series_key = key
                        break
            if series_key:
                for key, mult in _SERIES_MULTIPLIERS.items():
                    if key in series_key or series_key in key:
                        base *= mult
                        break

        # ── Age adjustment ────────────────────────────────────────────────────
        if year_built:
            age = 2024 - year_built
            if age > 40:
                base *= 0.85
            elif age > 20:
                base *= 0.93
            elif age < 5:
                base *= 1.10

        # ── Land value (houses only) ──────────────────────────────────────────
        # lot_size_sqft is actually sqm (post-Soviet standard despite the field name).
        # Uses realistic per-sqm land prices, not a flat $15 bonus.
        if lot_size_sqft and lot_size_sqft >= 50:
            land_price_per_sqm = _DEFAULT_LAND_PRICE_PER_SQM
            for key, val in _CITY_LAND_PRICE_PER_SQM.items():
                if key in city_key or city_key in key:
                    land_price_per_sqm = val
                    break

            # Central streets command a premium on land
            if any(street in addr_key for street in _CENTRAL_STREETS):
                land_price_per_sqm *= 1.80

            land_value = lot_size_sqft * land_price_per_sqm
            base += land_value
            logger.debug(
                "Land value: %d sqm × $%.0f/sqm = $%.0f",
                lot_size_sqft, land_price_per_sqm, land_value,
            )

        return max(base, 5_000)

    @staticmethod
    def _rental_yield(estimated_price: float, city: str = "") -> float:
        """
        Bishkek gross rental yield, district-aware.
        Central areas: lower yield (~5%), suburbs: higher (~8%).
        Source: house.kg rental analytics 2024.
        """
        if estimated_price <= 0:
            return 0.0
        city_lower = city.lower()
        # Monthly rent as % of property value, by district
        if any(k in city_lower for k in ("центр", "center", "филармония")):
            monthly_coeff = 0.004   # Central Bishkek ~4.8% annual
        elif city_lower.strip() in ("бишкек", "bishkek"):
            monthly_coeff = 0.0055  # Bishkek average ~6.6% annual
        elif city_lower.strip() in ("ош", "osh"):
            monthly_coeff = 0.006   # Osh ~7.2% annual
        else:
            monthly_coeff = 0.007   # Smaller cities / suburbs ~8.4% annual
        return round((monthly_coeff * 12) * 100, 1)

    @staticmethod
    def _appreciation(city: str, state: str) -> float:
        """
        Annual price appreciation estimate by city.
        Uses exact-match to avoid substring false positives (e.g. 'ош' in 'Пошта').
        """
        city_lower = city.lower().strip()
        if city_lower in ("бишкек", "bishkek"):
            return 9.5
        if city_lower in ("ош", "osh"):
            return 5.0
        if city_lower in ("джалал-абад", "jalal-abad", "каракол", "karakol"):
            return 4.8
        if city_lower in ("токмок", "tokmok", "кант", "kant"):
            return 3.5
        return 4.2

    @staticmethod
    def _fetch_comparables(
        city: str,
        bedrooms: int | None,
        listing_price: float | None,
    ) -> list[dict[str, Any]]:
        """
        Fetch real comparable listings from house.kg search.
        Returns empty list if scraping fails — never returns fake data.
        """
        from services.kg_scraper import scrape_comparables
        return scrape_comparables(city=city, bedrooms=bedrooms, listing_price=listing_price)
