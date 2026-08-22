"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import root_redirect

# OpenAPI / Swagger
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


urlpatterns = [
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # OpenAPI schema & documentation UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API
    path('api/v1/accounts/', include('accounts.api.v1.urls')),
    path('api/v1/posts/', include('posts.api.v1.urls')),
    path('api/v1/posts/<int:post_pk>/comments/', include('comments.api.v1.urls')),
    path('api/v1/hashtags/', include('hashtags.api.v1.urls')),
    path('api/v1/notifications/', include('notifications.api.v1.urls')),
    path('api/v1/dm/', include('direct_messages.api.v1.urls')),

    # Templates
    path('', include('accounts.urls')),
    path('', include('posts.urls')),
    path('', include('notifications.urls')),
    path('', include('direct_messages.urls')),
]

# serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
