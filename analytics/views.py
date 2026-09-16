from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .services import get_dashboard_summary


def analytics_dashboard(request: HttpRequest) -> HttpResponse:
    summary = get_dashboard_summary()
    return render(request, "analytics/dashboard.html", {"summary": summary, "title": "Аналитика"})
