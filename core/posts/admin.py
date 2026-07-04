from django.contrib import admin
from .models import Post, Like, Bookmark


class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'content', 'created_date']
    search_fields = ['content', 'author__email']
    list_filter = ['created_date']

admin.site.register(Post, PostAdmin)


class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_date']
    list_filter = ['created_date']

admin.site.register(Like, LikeAdmin)


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at']

admin.site.register(Bookmark, BookmarkAdmin)
