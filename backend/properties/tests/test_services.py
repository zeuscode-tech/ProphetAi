"""Unit tests for the PricingService."""

from unittest import TestCase

from services.pricing_service import PricingService


class PricingServiceTest(TestCase):
    def setUp(self):
        self.svc = PricingService()

    def test_predict_returns_expected_keys(self):
        result = self.svc.predict(
            bedrooms=3,
            bathrooms=2.0,
            square_feet=1500,
            city="Austin",
            state="TX",
        )
        for key in [
            "estimated_price",
            "investment_score",
            "rental_yield_pct",
            "appreciation_trend_pct",
            "comparable_sales",
            "confidence_interval",
        ]:
            self.assertIn(key, result)

    def test_estimated_price_positive(self):
        result = self.svc.predict(bedrooms=3, bathrooms=2.0, square_feet=1500)
        self.assertGreater(result["estimated_price"], 0)

    def test_investment_score_in_range(self):
        result = self.svc.predict(bedrooms=4, bathrooms=3.0, square_feet=2200)
        score = result["investment_score"]
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_confidence_interval_bounds(self):
        result = self.svc.predict(bedrooms=3, bathrooms=2.0, square_feet=1500)
        ci = result["confidence_interval"]
        self.assertLess(ci["low"], result["estimated_price"])
        self.assertGreater(ci["high"], result["estimated_price"])

    def test_comparables_count(self):
        result = self.svc.predict(bedrooms=3, bathrooms=2.0, square_feet=1500)
        self.assertEqual(len(result["comparable_sales"]), 5)

    def test_none_inputs_use_defaults(self):
        result = self.svc.predict(
            bedrooms=None, bathrooms=None, square_feet=None
        )
        self.assertGreater(result["estimated_price"], 0)
