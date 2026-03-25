"""Unit tests for ProphetAI models."""

from django.test import TestCase
from properties.models import Property, PropertyPhoto


class PropertyModelTest(TestCase):
    def setUp(self):
        self.prop = Property.objects.create(
            listing_url="https://example.com/listing/1",
            address="123 Main St",
            city="Austin",
            state="TX",
            listing_price=500_000,
            ai_estimated_price=525_000,
        )

    def test_str_returns_address(self):
        self.assertEqual(str(self.prop), "123 Main St")

    def test_price_delta_pct_positive(self):
        delta = self.prop.price_delta_pct
        self.assertIsNotNone(delta)
        self.assertAlmostEqual(delta, 5.0, places=1)

    def test_price_delta_pct_none_when_no_listing_price(self):
        self.prop.listing_price = None
        self.assertIsNone(self.prop.price_delta_pct)

    def test_default_status_is_pending(self):
        prop = Property(listing_url="https://example.com/listing/2")
        self.assertEqual(prop.status, Property.StatusChoices.PENDING)

    def test_photo_related_name(self):
        photo = PropertyPhoto.objects.create(
            property=self.prop,
            url="https://example.com/photo1.jpg",
        )
        self.assertIn(photo, self.prop.photos.all())


class PropertyPhotoModelTest(TestCase):
    def setUp(self):
        self.prop = Property.objects.create(
            listing_url="https://example.com/listing/photo-test"
        )
        self.photo = PropertyPhoto.objects.create(
            property=self.prop,
            url="https://example.com/photo.jpg",
            room_type="Kitchen",
            condition_score=7.5,
        )

    def test_str_contains_id(self):
        self.assertIn(str(self.photo.id), str(self.photo))
