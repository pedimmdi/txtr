from django.contrib import admin
from .models import Hashtag


class HashtagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

admin.site.register(Hashtag, HashtagAdmin)
