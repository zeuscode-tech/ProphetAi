"""Database models for ProphetAI property analysis."""

from django.db import models


class Property(models.Model):
    """Represents a real estate listing submitted for analysis."""

    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    # Listing metadata
    listing_url = models.URLField(unique=True, max_length=2048)
    address = models.CharField(max_length=512, blank=True, default="")
    city = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=64, blank=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    # Property features
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    square_feet = models.PositiveIntegerField(null=True, blank=True)
    lot_size_sqft = models.PositiveIntegerField(null=True, blank=True)
    year_built = models.PositiveSmallIntegerField(null=True, blank=True)
    listing_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # AI analysis results
    status = models.CharField(
        max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING
    )
    ai_estimated_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    investment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rental_yield_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    appreciation_trend_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    # Raw listing data from scraper
    listing_params = models.JSONField(default=dict, blank=True)  # All key-value params from the listing
    phone_number = models.CharField(max_length=64, blank=True, default="")
    map_lat = models.FloatField(null=True, blank=True)
    map_lng = models.FloatField(null=True, blank=True)

    # JSON fields for rich AI output
    red_flags = models.JSONField(default=list, blank=True)
    photo_insights = models.JSONField(default=list, blank=True)
    comparable_sales = models.JSONField(default=list, blank=True)
    gemini_raw_response = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    analysed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Property"
        verbose_name_plural = "Properties"

    def __str__(self) -> str:
        return self.address or self.listing_url

    @property
    def price_delta_pct(self) -> float | None:
        """
        Overpricing percentage: positive = listing is above market (bad for buyer),
        negative = listing is below market (good deal).
        Formula: (listing - estimate) / estimate * 100
        Example: $550k listing / $292k estimate → +88.2% (переплата)
        """
        if self.listing_price and self.ai_estimated_price and self.ai_estimated_price > 0:
            return float(
                (self.listing_price - self.ai_estimated_price) / self.ai_estimated_price * 100
            )
        return None


class PropertyPhoto(models.Model):
    """A photo associated with a property listing."""

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="photos"
    )
    url = models.URLField(max_length=2048)
    local_path = models.CharField(max_length=512, blank=True)
    gemini_analysis = models.JSONField(default=dict, blank=True)
    condition_score = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    room_type = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Photo {self.id} for {self.property}"
