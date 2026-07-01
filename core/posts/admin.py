from django.contrib import admin
from .models import Post


class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'created_date']
    search_fields = ['content', 'author__email']
    list_filter = ['created_date']

admin.site.register(Post, PostAdmin)
