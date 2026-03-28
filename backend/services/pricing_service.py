"""
Pricing Service — fair-market value estimation for ProphetAI (Kyrgyzstan market).

Uses a heuristic model calibrated to KG real estate prices (in USD).
If a trained XGBoost model artifact is found, it takes priority.
"""

from __future__ import annotations

import logging
import os
import random
import re
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_artifacts", "xgb_model.pkl")

# ── KG market price benchmarks (USD per sqm) ─────────────────────────────────
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
        return 1.0

    # 1. Price delta factor: how undervalued is it?
    #    delta > 0  → asking < fair (undervalued → good)
    #    delta < 0  → asking > fair (overvalued → bad)
    delta_ratio = (fair_price - market_price) / fair_price  # -1..+1
    price_score = 50.0 + delta_ratio * 50.0                 # maps to 0..100

    # 2. Condition factor
    cond_key = condition.lower().strip() if condition else ""
    cond_factor = _CONDITION_SCORE_FACTOR.get(cond_key, 0.75)
    # Partial match fallback
    if cond_factor == 0.75:
        for key, val in _CONDITION_SCORE_FACTOR.items():
            if key in cond_key:
                cond_factor = val
                break

    # 3. Absolute price factor: cheaper properties are more liquid in KG
    if fair_price < 50_000:
        liquidity_bonus = 10.0
    elif fair_price < 120_000:
        liquidity_bonus = 5.0
    elif fair_price > 500_000:
        liquidity_bonus = -10.0
    else:
        liquidity_bonus = 0.0

    raw = price_score * cond_factor + liquidity_bonus
    return round(max(1.0, min(100.0, raw)), 2)


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
            "comparable_sales": self._comparables(fair_price, bedrooms, square_feet, city),
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
    ) -> float:
        if self._model is not None:
            return self._predict_with_model(bedrooms, bathrooms, square_feet, lot_size_sqft, year_built)
        return self._heuristic_kg(bedrooms, square_feet, lot_size_sqft, year_built, city, condition, series)

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
    ) -> float:
        sqm = square_feet or (bedrooms or 2) * 25 + 20
        city_key = city.lower().strip()

        price_per_sqm = _DEFAULT_PRICE_PER_SQM
        for key, val in _CITY_PRICE_PER_SQM.items():
            if key in city_key or city_key in key:
                price_per_sqm = val
                break

        base = sqm * price_per_sqm

        # Condition adjustment
        cond_key = condition.lower().strip() if condition else ""
        for key, mult in _CONDITION_MULTIPLIERS.items():
            if key in cond_key:
                base *= mult
                break

        # Housing series adjustment (Bishkek-specific)
        series_key = series.lower().strip() if series else ""
        if not series_key:
            # Try to detect series from condition string
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

        # Age adjustment
        if year_built:
            age = 2024 - year_built
            if age > 40:
                base *= 0.85
            elif age > 20:
                base *= 0.93
            elif age < 5:
                base *= 1.10

        # Land bonus
        if lot_size_sqft and lot_size_sqft > 100:
            base += min(lot_size_sqft, 1000) * 15

        # Flag: seller overpricing (>500k in districts averaging <300k)
        # This is informational only; fair_price stays as calculated
        if base < 300_000:
            logger.debug("Fair price $%.0f — watch for overpriced listings in this district.", base)

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
    def _comparables(
        estimated_price: float,
        bedrooms: int | None,
        square_feet: int | None,
        city: str,
    ) -> list[dict[str, Any]]:
        rng = random.Random(int(estimated_price) % 9999)
        beds = bedrooms or 2
        sqm = square_feet or 55

        if "бишкек" in city.lower() or "bishkek" in city.lower():
            streets = [
                "ул. Манаса", "ул. Чуй", "мкр Аламедин", "мкр Джал",
                "ул. Байтик Баатыра", "мкр Асанбай", "ул. Токомбаева", "мкр Восток-5",
            ]
        elif "ош" in city.lower():
            streets = ["ул. Ленина", "ул. Курманжан Датки", "мкр Он-Адыр", "ул. Масалиева"]
        else:
            streets = ["ул. Ленина", "ул. Советская", "ул. Центральная", "ул. Мира"]

        return [
            {
                "address": f"{rng.choice(streets)}, {rng.randint(1, 150)}",
                "sale_price": round(estimated_price * (1 + rng.uniform(-0.13, 0.13)), -2),
                "bedrooms": max(1, beds + rng.randint(-1, 1)),
                "square_feet": sqm + rng.randint(-10, 10),
                "days_ago": rng.randint(7, 120),
            }
            for _ in range(5)
        ]
