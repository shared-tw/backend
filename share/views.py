from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from share import serializers


@extend_schema(
    request=serializers.CreateOrganizationSerializer,
    responses=serializers.OrganizationSerializer,
)
@api_view(http_method_names=["POST"])
def create_organization(request):
    serializer = serializers.CreateOrganizationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    instance = serializer.save()
    return Response(serializers.OrganizationSerializer(instance=instance).data)
