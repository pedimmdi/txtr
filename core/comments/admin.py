from django.contrib import admin
from .models import Comment, CommentLike


class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'parent', 'content', 'created_date']
    search_fields = ['content', 'author__email']
    list_filter = ['created_date']

admin.site.register(Comment, CommentAdmin)


class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment', 'created_at']
    list_filter = ['created_at']

admin.site.register(CommentLike, CommentLikeAdmin)
