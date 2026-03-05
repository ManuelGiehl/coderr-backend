from django.urls import path

from base_info_app.api.views import BaseInfoView

app_name = 'base_info_app'

urlpatterns = [
    path('', BaseInfoView.as_view()),
]
