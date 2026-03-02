from django.urls import path

from auth_app.api.views import LoginView, RegistrationView

app_name = 'auth_app'

urlpatterns = [
    path('registration/', RegistrationView.as_view()),
    path('login/', LoginView.as_view()),
]
