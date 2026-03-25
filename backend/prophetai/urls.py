"""URL configuration for the ProphetAI project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("properties.urls")),
]
