from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('zones/', include('zones.urls')),
    path('cache/', include('cache.urls')),
    path('config/', include('config.urls')),
    path('notifications/', include('notifications.urls')),
    path('users/', include('users.urls')),
]