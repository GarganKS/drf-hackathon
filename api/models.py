"""Роль «Моделі». Перші 30 хвилин дня цей файл пише вся команда разом.

Що має бути:
- елемент каталогу з числовим полем залишку (`PositiveIntegerField`);
- заявка: власник (FK на User), елемент (FK), кількість, `status`
  зі значеннями рівно `draft` / `confirmed` / `cancelled`;
- `CheckConstraint`, що залишок не від'ємний, — страхувальна сітка, а не головний захист.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    available = models.PositiveIntegerField()


class Meta:
    ordering = ["id"]
    constraints = [
        models.CheckConstraint(
            condition=Q(available__gte=0),
            name="book_available_nonnegative",
        ),
    ]


def __str__(self):
    return self.title


class LoanRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        CONFIRMED = "confirmed", "Підтверджено"
        CANCELLED = "cancelled", "Скасовано"

    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=9,
        choices=Status.choices,
        default=Status.DRAFT,
    )


class Meta:
    ordering = ["id"]
    constraints = [
        models.CheckConstraint(
            condition=Q(quantity__gte=1),
            name="loan_quantity_positive",
        ),
        models.CheckConstraint(
            condition=Q(status__in=["draft", "confirmed", "cancelled"]),
            name="loan_status_valid",
        ),
    ]
