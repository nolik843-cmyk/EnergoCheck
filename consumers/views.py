from __future__ import annotations

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import Q

from .models import Consumer
from .services import get_active_consumers


def is_employee(user) -> bool:
    return user.is_authenticated and user.is_employee


@login_required
@user_passes_test(is_employee)
def consumer_list(request: HttpRequest) -> HttpResponse:
    consumers = get_active_consumers()
    search = request.GET.get("q", "").strip()
    if search:
        consumers = consumers.filter(
            Q(account_number__icontains=search)
            | Q(full_name__icontains=search)
            | Q(address__icontains=search)
        )
    return render(request, "consumers/list.html", {"consumers": consumers, "search": search, "title": "Потребители"})


@login_required
@user_passes_test(is_employee)
def consumer_detail(request: HttpRequest, pk: int) -> HttpResponse:
    consumer = get_object_or_404(Consumer, pk=pk)
    readings = consumer.meter_readings.all()[:10]
    return render(
        request,
        "consumers/detail.html",
        {"consumer": consumer, "readings": readings, "title": consumer.full_name},
    )
