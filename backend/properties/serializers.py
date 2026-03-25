"""DRF serializers for the properties app."""

from rest_framework import serializers

from .models import Property, PropertyPhoto


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = [
            "id",
            "url",
            "gemini_analysis",
            "condition_score",
            "room_type",
            "created_at",
        ]


class PropertyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used in the dashboard list view."""

    price_delta_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "listing_url",
            "address",
            "city",
            "state",
            "bedrooms",
            "bathrooms",
            "square_feet",
            "listing_price",
            "ai_estimated_price",
            "investment_score",
            "status",
            "red_flags",
            "price_delta_pct",
            "created_at",
        ]


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Full serializer including photos and all AI analysis fields."""

    photos = PropertyPhotoSerializer(many=True, read_only=True)
    price_delta_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Property
        fields = "__all__"


class AnalyseURLSerializer(serializers.Serializer):
    """Input serializer for the analyse-by-URL endpoint."""

    listing_url = serializers.URLField(max_length=2048)
