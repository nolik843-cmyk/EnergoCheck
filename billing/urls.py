from django.urls import path

from .views import billing_dashboard, invoice_create_view, payment_create_view, tariff_create_view

urlpatterns = [
    path("", billing_dashboard, name="billing_dashboard"),
    path("invoice/create/", invoice_create_view, name="invoice_create"),
    path("tariffs/create/", tariff_create_view, name="tariff_create"),
    path("<int:invoice_id>/payment/create/", payment_create_view, name="payment_create"),
]
