from django.urls import path

from orders_app.api.views import OrderListView

app_name = 'orders_app'

urlpatterns = [
    path('', OrderListView.as_view()),
]
