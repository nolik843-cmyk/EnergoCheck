from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("consumers/", include("consumers.urls")),
    path("billing/", include("billing.urls")),
    path("analytics/", include("analytics.urls")),
    path("employee/", include("employee.urls")),
]
