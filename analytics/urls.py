from django.urls import path

from .views import analytics_dashboard, export_invoices_csv

urlpatterns = [
    path("", analytics_dashboard, name="analytics_dashboard"),
    path("invoices.csv", export_invoices_csv, name="analytics_invoices_csv"),
]
