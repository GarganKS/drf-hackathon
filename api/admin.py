from django.contrib import admin

from .models import Book, LoanRequest


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "available")


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "book", "owner", "quantity", "status")
    list_filter = ("status",)
