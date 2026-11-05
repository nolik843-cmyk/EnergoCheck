from django.urls import path

from .views import (
    anomaly_list_view,
    consumer_create_view,
    consumer_edit_view,
    contract_edit_view,
    meter_edit_view,
    supply_object_edit_view,
    contract_create_view,
    meter_create_view,
    meter_reading_create_view,
    meter_reading_review_action_view,
    meter_reading_review_view,
    photo_reading_create_view,
    supply_object_create_view,
)

urlpatterns = [
    path("consumers/create/", consumer_create_view, name="consumer_create"),
    path("consumers/<int:pk>/edit/", consumer_edit_view, name="consumer_edit"),
    path("objects/<int:pk>/edit/", supply_object_edit_view, name="supply_object_edit"),
    path("contracts/<int:pk>/edit/", contract_edit_view, name="contract_edit"),
    path("meters/<int:pk>/edit/", meter_edit_view, name="meter_edit"),
    path("objects/create/", supply_object_create_view, name="supply_object_create"),
    path("contracts/create/", contract_create_view, name="contract_create"),
    path("meters/create/", meter_create_view, name="meter_create"),
    path("readings/review/", meter_reading_review_view, name="meter_reading_review"),
    path("anomalies/", anomaly_list_view, name="anomaly_list"),
    path(
        "consumers/<int:consumer_id>/reading/photo/",
        photo_reading_create_view,
        name="photo_reading_create",
    ),
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
