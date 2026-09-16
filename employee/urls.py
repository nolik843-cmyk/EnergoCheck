from django.urls import path

from .views import consumer_create_view, meter_reading_create_view

urlpatterns = [
    path("consumers/create/", consumer_create_view, name="consumer_create"),
    path("consumers/<int:consumer_id>/reading/create/", meter_reading_create_view, name="meter_reading_create"),
]
