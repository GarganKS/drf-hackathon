"""Роль «API». Серіалізатори каталогу (Book) і заявки (LoanRequest)."""
from rest_framework import serializers

from .models import Book, LoanRequest

# Верхня межа кількості: щоб 99999999999999999999 давало 400, а не 500 від бази.
MAX_QUANTITY = 1_000_000


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "available"]


class LoanRequestSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1, max_value=MAX_QUANTITY)

    class Meta:
        model = LoanRequest
        fields = ["id", "book", "owner", "quantity", "status"]
        # Клієнт не може задати власника і стан: ігноруються, а не «сподіваємось».
        read_only_fields = ["owner", "status"]

    def validate(self, attrs):
        # Раннє відсікання (UX): кількість більша за залишок -> 400 одразу.
        # Це НЕ захист від гонки: остаточне рішення приймає умовний UPDATE у services.py.
        book = attrs.get("book") or (self.instance.book if self.instance else None)
        quantity = attrs.get("quantity") or (self.instance.quantity if self.instance else None)
        if book is not None and quantity is not None and quantity > book.available:
            raise serializers.ValidationError(
                {"quantity": f"Доступно лише {book.available} прим."}
            )
        return attrs
