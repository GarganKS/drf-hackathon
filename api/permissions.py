"""Роль «Доступ». Хто що може бачити і змінювати.

Покриває рядки 1–16 і 20 відкритої карти:

* каталог (Book) читає будь-хто, без токена (рядок 1), а змінює лише персонал:
  інакше клієнт сам «звільнив» би ресурс і зламав інваріант;
* усе, що стосується заявок, вимагає токена (рядки 2–4). `IsOrderOwner` разом із
  JWTAuthentication дає саме **401**, а не 403: DRF бере код із
  `authenticate_header()` першого автентифікатора;
* заявку бачить і змінює лише власник (рядки 7–10). Важливо: DRF НЕ викликає
  `has_object_permission` для списку, тому список окремо фільтрує `owner_queryset()`
  у `get_queryset()`. Чужа заявка для користувача просто не існує -> 404.

Стан заявки (draft/confirmed/cancelled) права НЕ перевіряють. Це робить база:
умовні UPDATE/DELETE у views.py і services.py, які повертають 409. Так перевірка
стану атомарна і не програє гонку.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """Каталог: читати може будь-хто, писати — лише персонал (is_staff)."""

    message = "Змінювати каталог може лише адміністратор."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class IsOrderOwner(BasePermission):
    """Заявки: потрібен токен, а окрема заявка доступна лише своєму власнику."""

    message = "Заявку бачить і змінює лише її власник."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and obj.owner_id is not None
            and obj.owner_id == user.pk
        )


def owner_queryset(queryset, user):
    """Заявки, які бачить конкретний користувач: лише його власні.

    Викликається з `get_queryset()`, бо `has_object_permission` не діє на список
    (рядок 7: чужі заявки не видно взагалі). Для аноніма — порожній набір.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return queryset.none()
    return queryset.filter(owner=user)
