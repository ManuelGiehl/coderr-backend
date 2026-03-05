from django.urls import path

from reviews_app.api.views import ReviewListView

app_name = 'reviews_app'

urlpatterns = [
    path('', ReviewListView.as_view()),
]
