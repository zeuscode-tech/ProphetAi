"""API views for the properties app."""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from services.gemini_service import GeminiService
from services.pricing_service import PricingService

from .models import Property
from .serializers import (
    AnalyseURLSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
)


class PropertyListView(generics.ListAPIView):
    """GET /api/properties/ — dashboard list of all analysed properties."""

    queryset = Property.objects.all()
    serializer_class = PropertyListSerializer


class PropertyDetailView(generics.RetrieveAPIView):
    """GET /api/properties/<pk>/ — full analysis detail for one property."""

    queryset = Property.objects.prefetch_related("photos")
    serializer_class = PropertyDetailSerializer


class AnalysePropertyView(APIView):
    """POST /api/analyse/ — submit a listing URL for AI analysis."""

    def post(self, request):
        serializer = AnalyseURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing_url = serializer.validated_data["listing_url"]

        # Return existing record if already analysed
        existing = Property.objects.filter(listing_url=listing_url).first()
        if existing and existing.status == Property.StatusChoices.COMPLETED:
            return Response(
                PropertyDetailSerializer(existing).data, status=status.HTTP_200_OK
            )

        # Create or reset the property record
        prop, _ = Property.objects.get_or_create(listing_url=listing_url)
        prop.status = Property.StatusChoices.PROCESSING
        prop.save(update_fields=["status"])

        try:
            # 1. Gemini: analyse listing page and photos
            gemini_svc = GeminiService()
            gemini_result = gemini_svc.analyse_listing(listing_url)

            # Persist extracted fields
            prop.address = gemini_result.get("address", "")
            prop.city = gemini_result.get("city", "")
            prop.state = gemini_result.get("state", "")
            prop.zip_code = gemini_result.get("zip_code", "")
            prop.bedrooms = gemini_result.get("bedrooms")
            prop.bathrooms = gemini_result.get("bathrooms")
            prop.square_feet = gemini_result.get("square_feet")
            prop.lot_size_sqft = gemini_result.get("lot_size_sqft")
            prop.year_built = gemini_result.get("year_built")
            prop.listing_price = gemini_result.get("listing_price")
            prop.red_flags = gemini_result.get("red_flags", [])
            prop.photo_insights = gemini_result.get("photo_insights", [])
            prop.gemini_raw_response = gemini_result

            # 2. Pricing model: estimate fair-market value
            pricing_svc = PricingService()
            pricing_result = pricing_svc.predict(
                bedrooms=prop.bedrooms,
                bathrooms=float(prop.bathrooms) if prop.bathrooms else None,
                square_feet=prop.square_feet,
                lot_size_sqft=prop.lot_size_sqft,
                year_built=prop.year_built,
                city=prop.city,
                state=prop.state,
                zip_code=prop.zip_code,
            )

            prop.ai_estimated_price = pricing_result.get("estimated_price")
            prop.investment_score = pricing_result.get("investment_score")
            prop.rental_yield_pct = pricing_result.get("rental_yield_pct")
            prop.appreciation_trend_pct = pricing_result.get("appreciation_trend_pct")
            prop.comparable_sales = pricing_result.get("comparable_sales", [])

            prop.status = Property.StatusChoices.COMPLETED
            prop.analysed_at = timezone.now()

        except Exception as exc:  # noqa: BLE001
            prop.status = Property.StatusChoices.FAILED
            prop.gemini_raw_response = {"error": str(exc)}

        prop.save()

        response_status = (
            status.HTTP_200_OK
            if prop.status == Property.StatusChoices.COMPLETED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(PropertyDetailSerializer(prop).data, status=response_status)
