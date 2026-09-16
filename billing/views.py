from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import Invoice


def billing_dashboard(request: HttpRequest) -> HttpResponse:
    invoices = Invoice.objects.select_related("consumer").all()
    return render(request, "billing/dashboard.html", {"invoices": invoices, "title": "Биллинг"})
