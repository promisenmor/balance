from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone

from .models import Budget, Transaction


def get_budget_period(period, on_date=None):
    on_date = on_date or timezone.localdate()

    if period == Budget.Period.WEEKLY:
        start = on_date - timedelta(days=on_date.weekday())
        end = start + timedelta(days=7)
    elif period == Budget.Period.MONTHLY:
        start = on_date.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1)
        else:
            end = date(start.year, start.month + 1, 1)
    elif period == Budget.Period.YEARLY:
        start = date(on_date.year, 1, 1)
        end = date(on_date.year + 1, 1, 1)
    else:
        raise ValueError(f"Unsupported budget period: {period}")

    return start, end


def get_budget_status(budget, on_date=None):
    start, end = get_budget_period(budget.period, on_date)
    spent = (
        Transaction.objects.filter(
            user=budget.user,
            transaction_type="expense",
            category__iexact=budget.category,
            transaction_date__gte=start,
            transaction_date__lt=end,
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    percent_used = (spent * 100 / budget.limit_amount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    alert_level = (
        "exceeded"
        if spent >= budget.limit_amount
        else "warning"
        if spent >= budget.limit_amount * Decimal("0.80")
        else "none"
    )

    return {
        "spent": spent,
        "remaining": budget.limit_amount - spent,
        "percent_used": percent_used,
        "alert_level": alert_level,
        "period_start": start,
        "period_end": end - timedelta(days=1),
    }
