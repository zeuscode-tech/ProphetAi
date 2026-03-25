"""Initial migration for the properties app."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies: list = []

    operations = [
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("listing_url", models.URLField(max_length=2048, unique=True)),
                ("address", models.CharField(blank=True, max_length=512)),
                ("city", models.CharField(blank=True, max_length=128)),
                ("state", models.CharField(blank=True, max_length=64)),
                ("zip_code", models.CharField(blank=True, max_length=20)),
                ("bedrooms", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("bathrooms", models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True)),
                ("square_feet", models.PositiveIntegerField(blank=True, null=True)),
                ("lot_size_sqft", models.PositiveIntegerField(blank=True, null=True)),
                ("year_built", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("listing_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("ai_estimated_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("investment_score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("rental_yield_pct", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("appreciation_trend_pct", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("red_flags", models.JSONField(blank=True, default=list)),
                ("photo_insights", models.JSONField(blank=True, default=list)),
                ("comparable_sales", models.JSONField(blank=True, default=list)),
                ("gemini_raw_response", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("analysed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Property",
                "verbose_name_plural": "Properties",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PropertyPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.URLField(max_length=2048)),
                ("local_path", models.CharField(blank=True, max_length=512)),
                ("gemini_analysis", models.JSONField(blank=True, default=dict)),
                ("condition_score", models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ("room_type", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="photos", to="properties.property")),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
