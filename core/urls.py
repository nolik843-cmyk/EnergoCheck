from django.urls import path

from .views import consumer_dashboard, employee_dashboard, home

urlpatterns = [
    path("", home, name="home"),
    path("employee/", employee_dashboard, name="employee_dashboard"),
    path("consumer/", consumer_dashboard, name="consumer_dashboard"),
]
