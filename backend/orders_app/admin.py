from django.contrib import admin

from orders_app.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'customer_user', 'business_user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('title',)
