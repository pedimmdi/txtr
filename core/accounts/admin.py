from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'created_date', 'is_active', 'is_staff']
    search_fields = ['email']
    ordering = ['created_date']

admin.site.register(User, CustomUserAdmin)
