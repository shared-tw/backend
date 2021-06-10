from django.urls import include, path
from rest_framework.routers import DefaultRouter

from share import views

router = DefaultRouter()
router.register(
    r"organization-required-items",
    views.OrganizationRequiredItemViewSet,
    basename="organization-required-items",
)

urlpatterns = [
    path("required-items/", views.RequiredItemList.as_view()),
    path("register/organization/", views.create_organization),
    path("register/donator/", views.create_donator),
    path("", include(router.urls)),
]
