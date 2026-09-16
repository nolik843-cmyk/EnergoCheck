from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum

from billing.models import Invoice, Payment
from consumers.models import Consumer


def get_dashboard_summary() -> dict[str, Decimal | int]:
    consumers = Consumer.objects.filter(is_active=True).count()
    total_billed = Invoice.objects.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    total_paid = Payment.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    overdue = Invoice.objects.filter(status=Invoice.Status.OVERDUE).count()
    return {
        "consumers": consumers,
        "total_billed": total_billed,
        "total_paid": total_paid,
        "overdue": overdue,
    }
