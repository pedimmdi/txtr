from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'created_date', 'is_active', 'is_staff']
    search_fields = ['email']
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    ordering = ['created_date']
    fieldsets = [
        ("Personal info", {'fields': [
            'email', 'password'
        ]}),
        ("Permissions", {'fields': [
            'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
        ]})
    ]
    add_fieldsets = [
        ("Create User", {'fields': [
            'email', 'password1', 'password2'
        ]})
    ]

admin.site.register(User, CustomUserAdmin)
