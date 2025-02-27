from django.urls import path
from . import views

urlpatterns = [
    path('', views.zone_list, name='zone_list'),
    path('<int:pk>/', views.zone_detail, name='zone_detail'),
    path('create/', views.zone_create, name='zone_create'),
    path('<int:pk>/edit/', views.zone_update, name='zone_update'),
    path('<int:pk>/delete/', views.zone_delete, name='zone_delete'),
]