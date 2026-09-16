from django.urls import path

from .views import billing_dashboard

urlpatterns = [
    path("", billing_dashboard, name="billing_dashboard"),
]
