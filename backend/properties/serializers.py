"""DRF serializers for the properties app."""

from rest_framework import serializers

from .models import Property, PropertyPhoto


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = ["id", "url", "gemini_analysis", "condition_score", "room_type", "created_at"]


class PropertyListSerializer(serializers.ModelSerializer):
    price_delta_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "listing_url", "address", "city", "state",
            "bedrooms", "bathrooms", "square_feet",
            "listing_price", "ai_estimated_price", "investment_score",
            "status", "red_flags", "price_delta_pct", "created_at",
        ]


class PropertyDetailSerializer(serializers.ModelSerializer):
    photos = PropertyPhotoSerializer(many=True, read_only=True)
    price_delta_pct = serializers.FloatField(read_only=True)
    # DRF serializes DecimalField as strings by default; cast to float for the frontend
    rental_yield_pct = serializers.FloatField(read_only=True)
    appreciation_trend_pct = serializers.FloatField(read_only=True)
    investment_score = serializers.FloatField(read_only=True)
    listing_price = serializers.FloatField(read_only=True)
    ai_estimated_price = serializers.FloatField(read_only=True)

    class Meta:
        model = Property
        exclude = ["gemini_raw_response"]  # Never send raw Gemini data (contains base64 images)


class AnalyseURLSerializer(serializers.Serializer):
    listing_url = serializers.URLField(max_length=2048)


class ProphetAIResponseSerializer(serializers.ModelSerializer):
    """
    Strict JSON output format for the ProphetAI analysis endpoint.

    Shape:
    {
        "property_title": str,
        "ai_estimate": float,
        "price_delta_percent": float,
        "investment_score": float,
        "condition": {"rating": 1-10, "style": str},
        "red_flags": [{"issue": str, "severity": "high|medium|low"}],
        "comparable_sales": [{"location": str, "price": float}],
        "images": [str]
    }
    """

    property_title = serializers.SerializerMethodField()
    ai_estimate = serializers.FloatField(source="ai_estimated_price")
    price_delta_percent = serializers.SerializerMethodField()
    investment_score = serializers.FloatField()
    condition = serializers.SerializerMethodField()
    red_flags = serializers.SerializerMethodField()
    comparable_sales = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "property_title",
            "ai_estimate",
            "price_delta_percent",
            "investment_score",
            "condition",
            "red_flags",
            "comparable_sales",
            "images",
        ]

    def get_property_title(self, obj: Property) -> str:
        parts = []
        if obj.address:
            parts.append(obj.address)
        if obj.city:
            parts.append(obj.city)
        if obj.bedrooms:
            parts.append(f"{obj.bedrooms}-комн.")
        if obj.square_feet:
            parts.append(f"{obj.square_feet} м²")
        return ", ".join(parts) if parts else obj.listing_url

    def get_price_delta_percent(self, obj: Property) -> float | None:
        """Positive = listing is undervalued, negative = overvalued."""
        return obj.price_delta_pct

    def get_condition(self, obj: Property) -> dict:
        raw = obj.gemini_raw_response or {}
        condition_block = raw.get("condition_analysis", {})

        rating = condition_block.get("repair_quality")
        style = condition_block.get("style", "")

        # Fallback: derive rating from photo_insights condition scores
        if rating is None:
            scores = [
                p.get("condition_score") or p.get("rating")
                for p in (obj.photo_insights or [])
                if isinstance(p, dict)
            ]
            scores = [s for s in scores if s is not None]
            rating = round(sum(scores) / len(scores), 1) if scores else None

        return {"rating": rating, "style": style or _infer_style(obj)}

    def get_red_flags(self, obj: Property) -> list[dict]:
        """
        Normalise red_flags from both old schema and new condition_analysis schema.
        Always returns [{"issue": str, "severity": "high|medium|low"}, ...].
        Adds smart overpricing flag if price delta is negative.
        """
        raw = obj.gemini_raw_response or {}

        # New schema: condition_analysis.red_flags
        flags = raw.get("condition_analysis", {}).get("red_flags", [])

        # Old schema fallback: top-level red_flags
        if not flags:
            flags = obj.red_flags or []

        result = []
        for f in flags:
            if not isinstance(f, dict):
                continue
            issue = f.get("issue") or f.get("category") or f.get("description", "")[:80]
            severity = (f.get("severity") or "medium").lower()
            if severity not in ("high", "medium", "low"):
                severity = "medium"
            result.append({"issue": issue, "severity": severity})

        # Auto-detect overpricing red flag
        delta = obj.price_delta_pct
        if delta is not None and delta < -10:
            result.append({
                "issue": f"Overpriced: Listing is {abs(delta):.0f}% above AI fair-market estimate. Interior condition may not match the price tier.",
                "severity": "high",
            })
        elif delta is not None and delta < -5:
            result.append({
                "issue": f"Slight overpricing: Listing is {abs(delta):.0f}% above estimated value.",
                "severity": "medium",
            })

        return result

    def get_comparable_sales(self, obj: Property) -> list[dict]:
        """Return comparable_sales in {address, sale_price, days_ago} shape."""
        sales = obj.comparable_sales or []
        return [
            {
                "address": s.get("address") or s.get("location", ""),
                "sale_price": s.get("sale_price") or s.get("price") or 0,
                "bedrooms": s.get("bedrooms", 0),
                "square_feet": s.get("square_feet", 0),
                "days_ago": s.get("days_ago", 0),
            }
            for s in sales
            if isinstance(s, dict)
        ]

    def get_images(self, obj: Property) -> list[str]:
        raw = obj.gemini_raw_response or {}

        # From photo_captions (new schema)
        captions = raw.get("photo_captions", [])
        if captions and isinstance(captions[0], dict) and "url" in captions[0]:
            return [c["url"] for c in captions if c.get("url")]

        # From photo_insights (old schema)
        insights = obj.photo_insights or []
        urls = [p.get("photo_url") or p.get("url") for p in insights if isinstance(p, dict)]
        urls = [u for u in urls if u]
        if urls:
            return urls

        # From related PropertyPhoto objects
        return [p.url for p in obj.photos.all()]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _infer_style(obj: Property) -> str:
    """Guess style from year_built if Gemini didn't return it."""
    if obj.year_built:
        if obj.year_built < 1991:
            return "soviet"
        if obj.year_built < 2005:
            return "classic"
        return "modern"
    return ""
