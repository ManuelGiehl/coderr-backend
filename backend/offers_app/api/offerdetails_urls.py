from django.urls import path

from offers_app.api.views import OfferDetailRetrieveView

app_name = 'offers_app_offerdetails'

urlpatterns = [
    path('<int:pk>/', OfferDetailRetrieveView.as_view()),
]
