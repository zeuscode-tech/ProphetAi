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
    PropertyDetailSerializer,
    PropertyListSerializer,
)

# Настраиваем логгер, чтобы видеть ошибки в терминале (важно для отладки VPN)
logger = logging.getLogger(__name__)

class PropertyListView(generics.ListAPIView):
    """GET /api/properties/ — список всех проанализированных объектов."""
    queryset = Property.objects.all().order_by('-created_at')
    serializer_class = PropertyListSerializer


class PropertyDetailView(generics.RetrieveAPIView):
    """GET /api/properties/<pk>/ — полная информация по одному объекту."""
    queryset = Property.objects.prefetch_related("photos")
    serializer_class = PropertyDetailSerializer


class AnalysePropertyView(APIView):
    """POST /api/analyse/ — отправка URL для AI анализа."""

    def post(self, request):
        serializer = AnalyseURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing_url = serializer.validated_data["listing_url"]

        # 1. Создаем запись или сбрасываем старую для повторного анализа
        prop, _ = Property.objects.get_or_create(listing_url=listing_url)
        prop.status = Property.StatusChoices.PROCESSING
        prop.save(update_fields=["status"])

        try:
            # 2. Вызов GeminiService
            gemini_svc = GeminiService()
            gemini_result = gemini_svc.analyse_listing(listing_url)

            # Проверка на пустой ответ (если VPN подвел или API недоступно)
            if not gemini_result or "error" in gemini_result:
                error_msg = gemini_result.get("error", "Unknown API error")
                raise ValueError(f"Gemini error: {error_msg}")

            # Безопасно сохраняем данные от нейросети через .get()
            prop.address = gemini_result.get("address", "")
            prop.city = gemini_result.get("city", "Бишкек")
            prop.state = gemini_result.get("state", "Чуйская область")
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

            # 3. Вызов PricingService (оборачиваем отдельно, чтобы не падал весь процесс)
            try:
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
                    condition=gemini_result.get("condition", ""),
                )

                prop.ai_estimated_price = pricing_result.get("estimated_price")
                prop.investment_score = pricing_result.get("investment_score")
                prop.rental_yield_pct = pricing_result.get("rental_yield_pct")
                prop.appreciation_trend_pct = pricing_result.get("appreciation_trend_pct")
                prop.comparable_sales = pricing_result.get("comparable_sales", [])
            except Exception as pricing_err:
                logger.warning(f"Ошибка в PricingService: {str(pricing_err)}")
                # Если математика не сработала, оставляем поля пустыми, но анализ Gemini сохраняем

            prop.status = Property.StatusChoices.COMPLETED
            prop.analysed_at = timezone.now()

        except Exception as exc:
            # Логируем ошибку, чтобы ты видел её в терминале
            logger.error(f"Критическая ошибка анализа: {str(exc)}")
            prop.status = Property.StatusChoices.FAILED
            # Сохраняем текст ошибки в базу для просмотра через админку
            prop.gemini_raw_response = {"error": str(exc)}

        # Финальное сохранение
        prop.save()

        # Формируем ответ
        response_status = (
            status.HTTP_200_OK
            if prop.status == Property.StatusChoices.COMPLETED
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(PropertyDetailSerializer(prop).data, status=response_status)