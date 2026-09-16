from django.urls import path

from .views import (
    consumer_create_view,
    contract_create_view,
    meter_create_view,
    meter_reading_create_view,
    meter_reading_review_action_view,
    meter_reading_review_view,
    supply_object_create_view,
)

urlpatterns = [
    path("consumers/create/", consumer_create_view, name="consumer_create"),
    path("objects/create/", supply_object_create_view, name="supply_object_create"),
    path("contracts/create/", contract_create_view, name="contract_create"),
    path("meters/create/", meter_create_view, name="meter_create"),
    path("readings/review/", meter_reading_review_view, name="meter_reading_review"),
    path(
        "readings/<int:reading_id>/review/",
        meter_reading_review_action_view,
        name="meter_reading_review_action",
    ),
    path(
        "consumers/<int:consumer_id>/reading/create/",
        meter_reading_create_view,
        name="meter_reading_create",
    ),
]
