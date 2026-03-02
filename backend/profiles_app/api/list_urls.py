from django.urls import path

from profiles_app.api.views import BusinessProfileListView, CustomerProfileListView

app_name = 'profiles_app_list'

urlpatterns = [
    path('business/', BusinessProfileListView.as_view()),
    path('customer/', CustomerProfileListView.as_view()),
]
