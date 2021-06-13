from django.urls import path

from .views import LineAuthCallbackView, LineAuthView

urlpatterns = [
    path("line/login", LineAuthView.as_view(), name="line-login"),
    path("line/callback", LineAuthCallbackView.as_view(), name="line-login-callback"),
]
