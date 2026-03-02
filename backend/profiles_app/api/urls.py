from django.urls import path

from profiles_app.api.views import ProfileDetailView

app_name = 'profiles_app'

urlpatterns = [
    path('<int:pk>/', ProfileDetailView.as_view()),
]
