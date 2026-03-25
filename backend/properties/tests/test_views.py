"""API endpoint tests for the properties app."""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from properties.models import Property


class PropertyListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Property.objects.create(
            listing_url="https://example.com/listing/1",
            address="123 Main St",
            status=Property.StatusChoices.COMPLETED,
            listing_price=400_000,
            ai_estimated_price=420_000,
            investment_score=68,
        )
        Property.objects.create(
            listing_url="https://example.com/listing/2",
            status=Property.StatusChoices.PENDING,
        )

    def test_list_returns_200(self):
        url = reverse("property-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_both_properties(self):
        url = reverse("property-list")
        response = self.client.get(url)
        self.assertEqual(response.data["count"], 2)

    def test_list_contains_expected_fields(self):
        url = reverse("property-list")
        response = self.client.get(url)
        result = response.data["results"][0]
        for field in ["id", "listing_url", "status", "investment_score"]:
            self.assertIn(field, result)


class PropertyDetailViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.prop = Property.objects.create(
            listing_url="https://example.com/listing/detail",
            address="456 Oak Ave",
            status=Property.StatusChoices.COMPLETED,
        )

    def test_detail_returns_200(self):
        url = reverse("property-detail", kwargs={"pk": self.prop.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_contains_address(self):
        url = reverse("property-detail", kwargs={"pk": self.prop.pk})
        response = self.client.get(url)
        self.assertEqual(response.data["address"], "456 Oak Ave")

    def test_detail_404_for_missing(self):
        url = reverse("property-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AnalysePropertyViewValidationTest(TestCase):
    """Test the analyse endpoint input validation (no real Gemini calls)."""

    def setUp(self):
        self.client = APIClient()

    def test_missing_url_returns_400(self):
        url = reverse("analyse-property")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_url_returns_400(self):
        url = reverse("analyse-property")
        response = self.client.post(
            url, {"listing_url": "not-a-url"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
