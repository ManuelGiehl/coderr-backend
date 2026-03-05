from django.urls import path

from orders_app.api.views import CompletedOrderCountView

app_name = 'orders_app_completed_order_count'

urlpatterns = [
    path('<int:business_user_id>/', CompletedOrderCountView.as_view()),
]
