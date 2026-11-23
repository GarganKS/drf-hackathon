"""Роль «API». ViewSet-и каталогу і заявок; @action confirm / cancel
викликають функції з services.py і нічого не рахують самі."""
from django.db import transaction
from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Book, LoanRequest
from .permissions import IsAdminOrReadOnly, IsOrderOwner, owner_queryset
from .serializers import BookSerializer, LoanRequestSerializer
from .services import Conflict


class BookViewSet(viewsets.ModelViewSet):
    """Каталог: читання відкрите, зміни лише для персоналу."""

    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:  # на книгу є заявки (PROTECT) -> 409, а не 500
            raise Conflict("Книгу не можна видалити: на неї є заявки.")


class LoanRequestViewSet(viewsets.ModelViewSet):
    """Заявки: лише з токеном і лише свої."""

    serializer_class = LoanRequestSerializer
    permission_classes = [IsOrderOwner]

    def get_queryset(self):
        # Чужі заявки просто не існують для користувача: список без них,
        # а detail/PATCH/DELETE/confirm чужої дають 404.
        return owner_queryset(
            LoanRequest.objects.select_related("book"), self.request.user
        )

    def perform_create(self, serializer):
        # Власник і стан — лише сервером; значення з тіла ігноруються.
        serializer.save(owner=self.request.user, status=LoanRequest.Status.DRAFT)

    def perform_update(self, serializer):
        # Інваріант: змінити book/quantity можна лише в draft. Для confirmed це
        # розсинхронізувало б списаний залишок із заявкою. Перевірка стану — в самому
        # UPDATE (filter status=draft), щоб не програти гонку з confirm.
        instance = serializer.instance
        data = serializer.validated_data
        if data:
            changed = LoanRequest.objects.filter(
                pk=instance.pk, status=LoanRequest.Status.DRAFT
            ).update(**data)
        else:
            changed = instance.status == LoanRequest.Status.DRAFT
        if not changed:
            raise Conflict("Редагувати можна лише чернетку.")
        instance.refresh_from_db()

    def perform_destroy(self, instance):
        # confirmed видаляти не можна (ресурс лишився б зайнятим без заявки).
        # Умова теж у самому DELETE, а не в Python.
        with transaction.atomic():
            deleted, _ = LoanRequest.objects.filter(
                pk=instance.pk,
                status__in=[LoanRequest.Status.DRAFT, LoanRequest.Status.CANCELLED],
            ).delete()
        if not deleted:
            raise Conflict("Підтверджену заявку спершу скасуйте.")

    # Схема станів і гонки — у services.py. 400/409 віддають його винятки.
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        loan = self.get_object()  # чужа -> 404
        loan = services.confirm_order(loan.pk, request.user)
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        loan = self.get_object()
        loan = services.cancel_order(loan.pk, request.user)
        return Response(self.get_serializer(loan).data)
