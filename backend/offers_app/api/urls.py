from django.urls import path

from offers_app.api.views import OfferDetailView, OfferListView

app_name = 'offers_app'

urlpatterns = [
    path('', OfferListView.as_view()),
    path('<int:pk>/', OfferDetailView.as_view()),
]
