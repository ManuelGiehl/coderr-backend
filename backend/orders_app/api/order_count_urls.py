from django.urls import path

from orders_app.api.views import OrderCountView

app_name = 'orders_app_order_count'

urlpatterns = [
    path('<int:business_user_id>/', OrderCountView.as_view()),
]
