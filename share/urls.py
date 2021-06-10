from django.urls import include, path

from share import views

urlpatterns = [
    path(r"register/orginization", views.create_organization),
]
