"""Роль «Стійкість». Уся бухгалтерія ресурсу — тут, а не у views.

    def confirm_order(order_id: int, user) -> Order: ...
    def cancel_order(order_id: int, user) -> Order: ...

Головне правило дня: ресурс зайнятий тоді й лише тоді, коли заявка в стані
`confirmed`. Кожна функція — одна `transaction.atomic()` і умовні UPDATE
(див. регламент, етап 2). Помилки віддавайте винятками, а views перетворять
їх на 400 / 409.
"""

"""Роль «Стійкість». Уся бухгалтерія ресурсу — тут, а не у views."""
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import APIException, ValidationError

from .models import Book, LoanRequest

S = LoanRequest.Status


class Conflict(APIException):
    status_code = 409
    default_detail = "Операція неможлива в поточному стані."
    default_code = "conflict"


def confirm_order(order_id, user):
    with transaction.atomic():
        # 1) стан: draft -> confirmed атомарно; 0 рядків = вже не draft
        if not LoanRequest.objects.filter(
            pk=order_id, owner=user, status=S.DRAFT
        ).update(status=S.CONFIRMED):
            raise Conflict("Підтвердити можна лише чернетку.")
        loan = LoanRequest.objects.get(pk=order_id)
        # 2) ресурс: списати лише якщо вистачає; 0 рядків = не вистачило
        if not Book.objects.filter(
            pk=loan.book_id, available__gte=loan.quantity
        ).update(available=F("available") - loan.quantity):
            raise ValidationError(
                {"quantity": "Недостатньо примірників."}
            )  # відкотить п.1
    return loan


def cancel_order(order_id, user):
    with transaction.atomic():
        qs = LoanRequest.objects.filter(pk=order_id, owner=user)
        if qs.filter(status=S.CONFIRMED).update(status=S.CANCELLED):
            loan = LoanRequest.objects.get(pk=order_id)
            Book.objects.filter(pk=loan.book_id).update(
                available=F("available") + loan.quantity
            )  # повертаємо рівно раз: лише той, хто виграв перехід
        elif not qs.filter(status=S.DRAFT).update(status=S.CANCELLED):
            raise Conflict("Заявку вже скасовано.")
    return LoanRequest.objects.get(pk=order_id)
