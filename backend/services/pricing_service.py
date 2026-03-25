"""
Pricing Service — fair-market value estimation for ProphetAI (Kyrgyzstan market).

Uses a heuristic model calibrated to KG real estate prices (in USD).
If a trained XGBoost model artifact is found, it takes priority.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_artifacts", "xgb_model.pkl")

# ── KG market price benchmarks (USD per sqm) ─────────────────────────────────
# Source: house.kg average 2023-2024
_CITY_PRICE_PER_SQM: dict[str, float] = {
    # Bishkek districts
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
    # Other cities
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
_DEFAULT_PRICE_PER_SQM = 700  # fallback if city unknown

# Condition multipliers
_CONDITION_MULTIPLIERS = {
    "новостройка": 1.20,
    "евроремонт": 1.15,
    "хорошее": 1.00,
    "среднее": 0.87,
    "требует ремонта": 0.70,
}


class PricingService:

    def __init__(self) -> None:
        self._model = self._load_model()

    def predict(
        self,
        bedrooms: int | None,
        bathrooms: float | None,
        square_feet: int | None,  # actually sqm in KG context
        lot_size_sqft: int | None = None,
        year_built: int | None = None,
        city: str = "",
        state: str = "",
        zip_code: str = "",
        condition: str = "",
    ) -> dict[str, Any]:
        estimated_price = self._estimate_price(
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
            lot_size_sqft=lot_size_sqft,
            year_built=year_built,
            city=city,
            condition=condition,
        )
        return {
            "estimated_price": round(estimated_price, 2),
            "investment_score": round(self._investment_score(estimated_price, year_built, square_feet), 2),
            "rental_yield_pct": round(self._rental_yield(estimated_price), 2),
            "appreciation_trend_pct": round(self._appreciation(city, state), 2),
            "comparable_sales": self._comparables(estimated_price, bedrooms, square_feet, city),
            "confidence_interval": {
                "low": round(estimated_price * 0.88, 2),
                "high": round(estimated_price * 1.12, 2),
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
    ) -> float:
        if self._model is not None:
            return self._predict_with_model(bedrooms, bathrooms, square_feet, lot_size_sqft, year_built)
        return self._heuristic_kg(bedrooms, square_feet, lot_size_sqft, year_built, city, condition)

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
    ) -> float:
        sqm = square_feet or (bedrooms or 2) * 25 + 20  # fallback if no area
        city_key = city.lower().strip()

        # Find price per sqm for city/district
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

        # Age adjustment (Soviet-era buildings ~1960-1990 get discount)
        if year_built:
            age = 2024 - year_built
            if age > 40:
                base *= 0.85
            elif age > 20:
                base *= 0.93
            elif age < 5:
                base *= 1.10  # new construction premium

        # Land bonus (for houses/cottages)
        if lot_size_sqft and lot_size_sqft > 100:
            base += min(lot_size_sqft, 1000) * 15  # ~$15/sqm land

        return max(base, 5_000)

    @staticmethod
    def _investment_score(estimated_price: float, year_built: int | None, square_feet: int | None) -> float:
        score = 50.0
        if square_feet and square_feet > 0:
            ppm = estimated_price / square_feet  # price per sqm
            if ppm < 500:
                score += 20
            elif ppm < 800:
                score += 10
            elif ppm > 1200:
                score -= 10
        if year_built:
            age = 2024 - year_built
            if age < 5:
                score += 15
            elif age < 15:
                score += 8
            elif age > 45:
                score -= 10
        return max(0.0, min(100.0, score))

    @staticmethod
    def _rental_yield(estimated_price: float) -> float:
        """Bishkek gross rental yield ~7-9% annually."""
        if estimated_price <= 0:
            return 0.0
        monthly_rent = estimated_price * 0.0065  # ~0.65% monthly
        return (monthly_rent * 12 / estimated_price) * 100

    @staticmethod
    def _appreciation(city: str, state: str) -> float:
        """Annual appreciation estimate. Bishkek ~8-12%, regions ~3-5%."""
        city_lower = city.lower()
        if "бишкек" in city_lower or "bishkek" in city_lower:
            return 9.5
        if "ош" in city_lower or "osh" in city_lower:
            return 5.0
        return 4.0

    @staticmethod
    def _comparables(
        estimated_price: float,
        bedrooms: int | None,
        square_feet: int | None,
        city: str,
    ) -> list[dict[str, Any]]:
        """Generate synthetic comparable sales based on city context."""
        rng = random.Random(int(estimated_price) % 9999)
        beds = bedrooms or 2
        sqm = square_feet or 55

        # KG street name samples per city
        if "бишкек" in city.lower() or "bishkek" in city.lower():
            streets = ["ул. Манаса", "ул. Чуй", "мкр Аламедин", "мкр Джал", "ул. Байтик Баатыра",
                       "мкр Асанбай", "ул. Токомбаева", "мкр Восток-5"]
        elif "ош" in city.lower():
            streets = ["ул. Ленина", "ул. Курманжан Датки", "мкр Он-Адыр", "ул. Масалиева"]
        else:
            streets = ["ул. Ленина", "ул. Советская", "ул. Центральная", "ул. Мира"]

        comps = []
        for i in range(5):
            spread = rng.uniform(-0.13, 0.13)
            comps.append({
                "address": f"{rng.choice(streets)}, {rng.randint(1, 150)}",
                "sale_price": round(estimated_price * (1 + spread), -2),
                "bedrooms": max(1, beds + rng.randint(-1, 1)),
                "square_feet": sqm + rng.randint(-10, 10),
                "days_ago": rng.randint(7, 120),
            })
        return comps
