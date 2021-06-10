from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from share import models, serializers


class RequiredItemList(generics.ListAPIView):
    queryset = models.RequiredItem.objects.all()
    serializer_class = serializers.RequiredItemSerializer
    authentication_classes = []


class OrganizationRequiredItemViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    serializer_class = serializers.RequiredItemSerializer

    def get_queryset(self):
        return models.RequiredItem.objects.filter(
            organization=self.request.user.organization
        )

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


@extend_schema(
    request=serializers.CreateOrganizationSerializer,
    responses=serializers.OrganizationSerializer,
)
@api_view(http_method_names=["POST"])
@authentication_classes([])
def create_organization(request):
    serializer = serializers.CreateOrganizationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    return Response(serializers.OrganizationSerializer(instance=instance).data)


@extend_schema(
    request=serializers.CreateDonatorSerializer,
    responses=serializers.DonatorSerializer,
)
@api_view(http_method_names=["POST"])
@authentication_classes([])
def create_donator(request):
    serializer = serializers.CreateDonatorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    return Response(serializers.DonatorSerializer(instance=instance).data)
