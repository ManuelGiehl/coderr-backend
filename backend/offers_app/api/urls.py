from django.urls import path

from offers_app.api.views import OfferListView

app_name = 'offers_app'

urlpatterns = [
    path('', OfferListView.as_view()),
]
