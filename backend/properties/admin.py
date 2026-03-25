"""Django admin for the properties app."""

from django.contrib import admin

from .models import Property, PropertyPhoto


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 0
    readonly_fields = ("gemini_analysis", "condition_score", "room_type")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "address",
        "city",
        "state",
        "listing_price",
        "ai_estimated_price",
        "investment_score",
        "status",
        "created_at",
    )
    list_filter = ("status", "state")
    search_fields = ("address", "city", "listing_url")
    readonly_fields = ("created_at", "updated_at", "analysed_at", "gemini_raw_response")
    inlines = [PropertyPhotoInline]


@admin.register(PropertyPhoto)
class PropertyPhotoAdmin(admin.ModelAdmin):
    list_display = ("property", "room_type", "condition_score", "created_at")
    list_filter = ("room_type",)
