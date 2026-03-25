"""
Pricing Service — XGBoost-based fair-market value prediction for ProphetAI.

In production, this service would load a pre-trained XGBoost model from disk.
The placeholder implementation uses a simple heuristic model so the API remains
functional even without a trained model artifact.
"""

from __future__ import annotations

import logging
import math
import os
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Path where the trained model pickle is expected
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_artifacts", "xgb_model.pkl")


class PricingService:
    """
    Estimates fair-market value and computes investment metrics.

    If a trained XGBoost model artifact is found at ``_MODEL_PATH``, it will
    be used for prediction.  Otherwise, a transparent heuristic baseline is
    applied so that the service always returns a sensible result.
    """

    def __init__(self) -> None:
        self._model = self._load_model()

    # ──────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────

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
    ) -> dict[str, Any]:
        """
        Return a pricing analysis dictionary with keys:
        - estimated_price (float)
        - investment_score (float, 0–100)
        - rental_yield_pct (float)
        - appreciation_trend_pct (float)
        - comparable_sales (list of dicts)
        - confidence_interval (dict with "low" and "high")
        """
        estimated_price = self._estimate_price(
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
            lot_size_sqft=lot_size_sqft,
            year_built=year_built,
        )

        investment_score = self._compute_investment_score(
            estimated_price=estimated_price,
            year_built=year_built,
            square_feet=square_feet,
        )

        rental_yield = self._estimate_rental_yield(estimated_price)
        appreciation = self._estimate_appreciation(state=state, zip_code=zip_code)
        comparables = self._generate_comparables(estimated_price, bedrooms, square_feet)
        ci = self._confidence_interval(estimated_price)

        return {
            "estimated_price": round(estimated_price, 2),
            "investment_score": round(investment_score, 2),
            "rental_yield_pct": round(rental_yield, 2),
            "appreciation_trend_pct": round(appreciation, 2),
            "comparable_sales": comparables,
            "confidence_interval": ci,
        }

    # ──────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _load_model() -> Any | None:
        """Attempt to load a pickled XGBoost model from disk."""
        if not os.path.exists(_MODEL_PATH):
            logger.info("No trained model found at %s; using heuristic baseline.", _MODEL_PATH)
            return None
        try:
            import pickle

            with open(_MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            logger.info("Loaded XGBoost model from %s.", _MODEL_PATH)
            return model
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load model: %s", exc)
            return None

    def _estimate_price(
        self,
        bedrooms: int | None,
        bathrooms: float | None,
        square_feet: int | None,
        lot_size_sqft: int | None,
        year_built: int | None,
    ) -> float:
        """Estimate fair-market value using a trained model or heuristic fallback."""
        if self._model is not None:
            return self._predict_with_model(
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                year_built=year_built,
            )
        return self._heuristic_estimate(
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
            lot_size_sqft=lot_size_sqft,
            year_built=year_built,
        )

    def _predict_with_model(
        self,
        bedrooms: int | None,
        bathrooms: float | None,
        square_feet: int | None,
        lot_size_sqft: int | None,
        year_built: int | None,
    ) -> float:
        """Run inference through the XGBoost model."""
        features = np.array(
            [[
                bedrooms or 3,
                bathrooms or 2.0,
                square_feet or 1500,
                lot_size_sqft or 5000,
                year_built or 2000,
            ]],
            dtype=np.float32,
        )
        return float(self._model.predict(features)[0])

    @staticmethod
    def _heuristic_estimate(
        bedrooms: int | None,
        bathrooms: float | None,
        square_feet: int | None,
        lot_size_sqft: int | None,
        year_built: int | None,
    ) -> float:
        """
        Simple but transparent heuristic using US national averages:
        ~$175/sqft base, adjusted for age, lot, bedrooms, and bathrooms.
        """
        sqft = square_feet or 1500
        beds = bedrooms or 3
        baths = bathrooms or 2.0
        lot = lot_size_sqft or 5000
        age = max(0, 2024 - (year_built or 2000))

        base = sqft * 175.0
        bed_bonus = beds * 8_000
        bath_bonus = baths * 6_000
        lot_bonus = min(lot, 43560) * 0.80  # Cap at 1 acre; $0.80/sqft
        age_discount = min(age * 500, 50_000)  # Up to $50k discount for age

        return max(base + bed_bonus + bath_bonus + lot_bonus - age_discount, 50_000)

    @staticmethod
    def _compute_investment_score(
        estimated_price: float,
        year_built: int | None,
        square_feet: int | None,
    ) -> float:
        """Composite 0–100 investment score (higher = better opportunity)."""
        score = 50.0  # Neutral baseline

        # Price-per-sqft efficiency (lower is better for buyer)
        if square_feet and square_feet > 0:
            price_per_sqft = estimated_price / square_feet
            if price_per_sqft < 100:
                score += 20
            elif price_per_sqft < 175:
                score += 10
            elif price_per_sqft > 350:
                score -= 10

        # Newer homes get bonus; very old homes get penalty
        if year_built:
            age = 2024 - year_built
            if age < 10:
                score += 10
            elif age < 30:
                score += 5
            elif age > 50:
                score -= 5

        return max(0.0, min(100.0, score))

    @staticmethod
    def _estimate_rental_yield(estimated_price: float) -> float:
        """Rough gross rental yield estimate (~6% national average)."""
        if estimated_price <= 0:
            return 0.0
        monthly_rent_estimate = estimated_price * 0.006  # 0.6% monthly gross rule
        annual_rent = monthly_rent_estimate * 12
        return (annual_rent / estimated_price) * 100

    @staticmethod
    def _estimate_appreciation(state: str, zip_code: str) -> float:
        """Placeholder annual appreciation estimate (national ~4% avg)."""
        # In production: query a real appreciation API or historical DB
        return 4.2

    @staticmethod
    def _generate_comparables(
        estimated_price: float, bedrooms: int | None, square_feet: int | None
    ) -> list[dict[str, Any]]:
        """Generate synthetic comparable sales entries for UI demonstration."""
        import random

        rng = random.Random(int(estimated_price) % 9999)
        beds = bedrooms or 3
        sqft = square_feet or 1500
        comps = []
        for i in range(5):
            spread = rng.uniform(-0.12, 0.12)
            comps.append({
                "address": f"{rng.randint(100, 9999)} Sample St #{i + 1}",
                "sale_price": round(estimated_price * (1 + spread), -2),
                "bedrooms": beds + rng.randint(-1, 1),
                "square_feet": sqft + rng.randint(-200, 200),
                "days_ago": rng.randint(14, 180),
            })
        return comps

    @staticmethod
    def _confidence_interval(estimated_price: float) -> dict[str, float]:
        """±12% confidence interval around the estimate."""
        margin = estimated_price * 0.12
        return {
            "low": round(estimated_price - margin, 2),
            "high": round(estimated_price + margin, 2),
        }
