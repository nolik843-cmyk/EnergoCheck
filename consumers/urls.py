from django.urls import path

from .views import consumer_detail, consumer_list

urlpatterns = [
    path("", consumer_list, name="consumer_list"),
    path("<int:pk>/", consumer_detail, name="consumer_detail"),
]
