"""API views for the properties app."""

import logging
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from services.gemini_service import GeminiService
from services.pricing_service import PricingService

from .models import Property
from .serializers import (
    AnalyseURLSerializer,
    ProphetAIResponseSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
)

logger = logging.getLogger(__name__)


class PropertyListView(generics.ListAPIView):
    """GET /api/properties/ — список всех проанализированных объектов."""
    queryset = Property.objects.all().order_by("-created_at")
    serializer_class = PropertyListSerializer


class PropertyDetailView(generics.RetrieveAPIView):
    """GET /api/properties/<pk>/ — полная информация по одному объекту."""
    queryset = Property.objects.prefetch_related("photos")
    serializer_class = PropertyDetailSerializer


class AnalysePropertyView(APIView):
    """
    POST /api/analyse/
    Body: {"listing_url": "https://house.kg/..."}

    Returns the strict ProphetAI JSON:
    {
        "property_title", "ai_estimate", "price_delta_percent",
        "investment_score", "condition", "red_flags",
        "comparable_sales", "images"
    }
    """

    def post(self, request):
        serializer = AnalyseURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing_url = serializer.validated_data["listing_url"]

        prop, _ = Property.objects.get_or_create(listing_url=listing_url)
        prop.status = Property.StatusChoices.PROCESSING
        prop.save(update_fields=["status"])

        try:
            # ── Step 1: Gemini multimodal analysis ───────────────────────────
            gemini_svc = GeminiService()
            gemini_result = gemini_svc.analyse_listing(listing_url)

            if not gemini_result or "error" in gemini_result:
                raise ValueError(f"Gemini error: {gemini_result.get('error', 'Unknown')}")

            # ── Step 2: Map Gemini fields → model ────────────────────────────
            prop.address      = gemini_result.get("address", "")
            prop.city         = gemini_result.get("city", "Бишкек")
            prop.state        = gemini_result.get("state", "Чуйская область")
            prop.zip_code     = gemini_result.get("zip_code", "")
            prop.bedrooms     = gemini_result.get("bedrooms")
            prop.bathrooms    = gemini_result.get("bathrooms")
            prop.square_feet  = gemini_result.get("square_feet")
            prop.lot_size_sqft = gemini_result.get("lot_size_sqft")
            prop.year_built   = gemini_result.get("year_built")
            prop.listing_price = gemini_result.get("listing_price")

            condition_block = gemini_result.get("condition_analysis", {})
            prop.red_flags    = condition_block.get("red_flags", [])
            prop.photo_insights = gemini_result.get("photo_captions", [])
            prop.gemini_raw_response = gemini_result

            # Gemini valuation/investment as fallbacks
            gemini_valuation  = gemini_result.get("valuation", {})
            gemini_inv        = gemini_result.get("investment_potential", {})

            # ── Step 3: PricingService (KG heuristic / XGBoost) ──────────────
            try:
                pricing_svc = PricingService()
                pricing_result = pricing_svc.predict(
                    bedrooms      = prop.bedrooms,
                    bathrooms     = float(prop.bathrooms) if prop.bathrooms else None,
                    square_feet   = prop.square_feet,
                    lot_size_sqft = prop.lot_size_sqft,
                    year_built    = prop.year_built,
                    city          = prop.city,
                    state         = prop.state,
                    zip_code      = prop.zip_code,
                    condition     = gemini_result.get("condition", ""),
                    listing_price = float(prop.listing_price) if prop.listing_price else None,
                )

                prop.ai_estimated_price    = pricing_result["estimated_price"]
                prop.investment_score      = pricing_result["investment_score"]
                prop.rental_yield_pct      = pricing_result["rental_yield_pct"]
                prop.appreciation_trend_pct = pricing_result["appreciation_trend_pct"]
                prop.comparable_sales      = pricing_result["comparable_sales"]

            except Exception as pricing_err:
                logger.warning("PricingService failed: %s", pricing_err)
                # Fallback to Gemini's own estimates
                prop.ai_estimated_price = gemini_valuation.get("estimated_price")
                prop.investment_score   = gemini_inv.get("score")

            # ── Step 4: Ensure no blanks — fallback defaults ─────────────────
            if not prop.rental_yield_pct and prop.ai_estimated_price:
                est = float(prop.ai_estimated_price)
                market = float(prop.listing_price or est)
                if market > 0:
                    city_lower = (prop.city or "").lower()
                    # District-aware monthly rent coefficients (% of property value)
                    # Central areas: lower yield but higher liquidity
                    # Suburban areas: higher yield but lower demand
                    if any(k in city_lower for k in ("центр", "center", "филармония")):
                        monthly_coeff = 0.004   # ~4.8% annual
                    elif any(k in city_lower for k in ("бишкек", "bishkek")):
                        monthly_coeff = 0.0055  # ~6.6% annual
                    elif any(k in city_lower for k in ("ош", "osh")):
                        monthly_coeff = 0.006   # ~7.2% annual
                    else:
                        monthly_coeff = 0.007   # ~8.4% annual (smaller cities/suburbs)
                    prop.rental_yield_pct = round(
                        (est * monthly_coeff * 12) / market * 100, 1
                    )

            if not prop.appreciation_trend_pct:
                city_lower = (prop.city or "").lower()
                # Use city-level estimates; exact match to avoid substring false positives
                if city_lower.strip() in ("бишкек", "bishkek"):
                    prop.appreciation_trend_pct = 9.5
                elif city_lower.strip() in ("ош", "osh"):
                    prop.appreciation_trend_pct = 5.0
                elif city_lower.strip() in ("джалал-абад", "jalal-abad", "каракол", "karakol"):
                    prop.appreciation_trend_pct = 4.8
                else:
                    prop.appreciation_trend_pct = 4.2

            # If no comparable sales from PricingService, leave empty —
            # frontend will show "Нет данных" instead of fake addresses.

            prop.status      = Property.StatusChoices.COMPLETED
            prop.analysed_at = timezone.now()

        except Exception as exc:
            logger.error("Analysis failed for %s: %s", listing_url, exc)
            prop.status = Property.StatusChoices.FAILED
            prop.gemini_raw_response = {"error": str(exc)}

        prop.save()

        if prop.status == Property.StatusChoices.COMPLETED:
            http_status = status.HTTP_200_OK
        elif prop.status == Property.StatusChoices.FAILED:
            http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
        else:
            # PROCESSING / PENDING — analysis in progress
            http_status = status.HTTP_202_ACCEPTED

        return Response(
            PropertyDetailSerializer(prop).data,
            status=http_status,
        )
