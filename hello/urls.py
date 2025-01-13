from django.urls import path
from . import views

app_name = "hello"

urlpatterns = [
    #path('cookie', views.cookie),
    #path('sessfun', views.sessfun),
    path('', views.IndexView.as_view(), name="hello"),  # This is the URL pattern for /hello/
]
