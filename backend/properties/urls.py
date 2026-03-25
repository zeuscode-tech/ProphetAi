"""URL routes for the properties app."""

from django.urls import path

from .views import AnalysePropertyView, PropertyDetailView, PropertyListView

urlpatterns = [
    path("properties/", PropertyListView.as_view(), name="property-list"),
    path("properties/<int:pk>/", PropertyDetailView.as_view(), name="property-detail"),
    path("analyse/", AnalysePropertyView.as_view(), name="analyse-property"),
]
