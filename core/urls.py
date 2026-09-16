from django.urls import path

from .views import employee_dashboard, home

urlpatterns = [
    path("", home, name="home"),
    path("employee/", employee_dashboard, name="employee_dashboard"),
]
