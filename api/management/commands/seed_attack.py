"""Роль «Моделі». Готує базу до атаки; запускати можна скільки завгодно разів.

    python manage.py migrate
    python manage.py seed_attack

Атакувальник клонує ваш репозиторій на тегу `attack` і запускає саме ці дві команди,
тож усе, без чого атака неможлива, має створюватися тут.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.models import Book

# Ті самі паролі — у contract.json.
ATTACKERS = {"attacker1": "attack-pass-1", "attacker2": "attack-pass-2"}

# Фіксований id елемента для гонки: його значення йде в contract.json як race_item.
RACE_ITEM_ID = 1000
REGULAR_STOCK = 50

REGULAR_BOOKS = [
    ("Кобзар", "Тарас Шевченко"),
    ("Лісова пісня", "Леся Українка"),
    ("Тіні забутих предків", "Михайло Коцюбинський"),
    ("Захар Беркут", "Іван Франко"),
    ("Intermezzo", "Михайло Коцюбинський"),
]


class Command(BaseCommand):
    help = "Акаунти attacker1/attacker2 і каталог для атаки."

    def handle(self, *args, **options):
        User = get_user_model()
        for username, password in ATTACKERS.items():
            user, _ = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.save()

        # update_or_create: повторний запуск відновлює залишок до початкового.
        for title, author in REGULAR_BOOKS:
            Book.objects.update_or_create(
                title=title,
                defaults={"author": author, "available": REGULAR_STOCK},
            )

        # Елемент для гонки: залишок рівно 1, id фіксований -> race_item у contract.json.
        Book.objects.update_or_create(
            pk=RACE_ITEM_ID,
            defaults={"title": "Книга для гонки", "author": "Автор", "available": 1},
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: attacker1, attacker2, каталог. race_item = {RACE_ITEM_ID}"
            )
        )
