"""Роль «Доступ». Власні класи прав, власник заявки, коди відповідей.

Покриває рядки 1–16 і 20 відкритої карти:

* каталог читається без токена (рядок 1), але його заборонено змінювати —
  інакше клієнт міг би сам «звільнити» ресурс і зламати інваріант;
* усе, що стосується заявок, вимагає токена (рядки 2–4). Перевірка
  `IsAuthenticated` разом із JWTAuthentication (перший у
  `DEFAULT_AUTHENTICATION_CLASSES`) дає саме **401**, а не 403 — бо DRF
  бере код з `authenticate_header()` першого автентифікатора;
* заявку бачить і змінює **лише власник** (рядки 7–10). Важливо:
  `has_object_permission` НЕ викликається для списку, тому список окремо
  фільтрує `owner_queryset()` у `get_queryset()` viewset-а;
* стан і власника клієнт не задає — це read-only серіалізатора
  (рядки 11–12), але права тут теж не дають змінювати вже підтверджену
  заявку, бо це порушило б інваріант «ресурс зайнятий ⇔ confirmed».

Як це підключити (роль «API», файли `views.py` / `serializers.py`)::

    class LoanRequestViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticatedOrderOwner, IsDraftOrReadOnly]

        def get_queryset(self):
            return owner_queryset(LoanRequest.objects.all(), self.request.user)

        def perform_create(self, serializer):
            serializer.save(owner=self.request.user)  # owner з тіла ігнорується

    class BookViewSet(viewsets.ReadOnlyModelViewSet):
        permission_classes = [IsCatalogReadOnly]

`confirm` / `cancel` — це `@action(detail=True)`, тож для них теж
викликається `has_object_permission`. `IsDraftOrReadOnly` свідомо
пропускає ці дії: їхню схему станів і коди 409 перевіряє роль «Стійкість».
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

# Дії, стан яких перевіряє services.py, а не шар прав. Якщо не виключити
# їх тут, повторний confirm отримав би 403 замість очікуваних 409.
_STATE_ACTIONS = frozenset({"confirm", "cancel"})


class IsCatalogReadOnly(BasePermission):
    """Каталог (Books) — читати можна всім, писати — нікому.

    Рядок 1 карти: GET без токена → 200. Зміна залишку через API заборонена:
    ресурс займає тільки confirm, а повертає тільки cancel.
    """

    message = "Каталог доступний лише для читання."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsAuthenticatedOrderOwner(BasePermission):
    """Заявки: потрібен токен, а об'єкт доступний тільки своєму власнику.

    Рядки 2–4 (Без токена → 401) і 7–10 (чужа заявка → 403/404).
    Для списку цей клас не фільтрує — це робить `owner_queryset()`.
    """

    message = "Заявку бачить і змінює лише її власник."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        owner_id = getattr(obj, "owner_id", None)
        user = request.user
        if owner_id is None or not user or not user.is_authenticated:
            return False
        return owner_id == user.pk


class IsDraftOrReadOnly(BasePermission):
    """Додатковий замок на інваріант для PATCH/PUT/DELETE заявки.

    Читати свою заявку можна в будь-якому стані. Змінювати або видаляти —
    тільки поки вона `draft`: після confirm залишок уже списано, і PATCH
    quantity чи DELETE зіпсували б співвідношення «залишок ⇔ confirmed».
    Кінцевий стан `cancelled` теж не міняється.

    `confirm` / `cancel` exemption: ці POST-и обробляє services.py, який
    сам повертає 409 на некоректний перехід (рядки 18–19).
    """

    message = "Змінювати можна лише заявку в стані draft."

    def has_permission(self, request, view):
        # Автентифікацію перевіряє IsAuthenticatedOrderOwner, щоб без токена
        # лишався саме 401. Тут не відмовляємо нікому зайве.
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if getattr(view, "action", None) in _STATE_ACTIONS:
            return True
        return getattr(obj, "status", None) == "draft"


def owner_queryset(queryset, user):
    """Список заявок, який бачить конкретний користувач.

    Викликається з `get_queryset()` — саме тут, а не в
    `has_object_permission`, бо DRF не перевіряє права на кожен рядок
    списку (рядок 7: чужі заявки не видно взагалі).

    Для аноніма повертає порожній набір: доступ закритий ще до того, як
    DRF дійде до перевірки прав.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return queryset.none()
    return queryset.filter(owner=user)
