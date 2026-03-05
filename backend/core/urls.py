"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/base-info/', include('base_info_app.api.urls')),
    path('api/offers/', include('offers_app.api.urls')),
    path('api/offerdetails/', include('offers_app.api.offerdetails_urls')),
    path('api/orders/', include('orders_app.api.urls')),
    path('api/order-count/', include('orders_app.api.order_count_urls')),
    path('api/completed-order-count/', include('orders_app.api.completed_order_count_urls')),
    path('api/profile/', include('profiles_app.api.urls')),
    path('api/profiles/', include('profiles_app.api.list_urls')),
    path('api/reviews/', include('reviews_app.api.urls')),
    path('api/', include('auth_app.api.urls')),
]
