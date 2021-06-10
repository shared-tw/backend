from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from rest_framework import exceptions, serializers

from .models import Organization

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class CreateOrganizationSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    name = serializers.CharField()
    password = serializers.CharField()
    confirmed_password = serializers.CharField()

    def create(self, validated_data):
        if validated_data["password"] != validated_data["confirmed_password"]:
            raise exceptions.ValidationError("Password doesn't match.")

        username = validated_data.pop("username")
        try:
            user = User.objects.create_user(
                username=username, password=validated_data.pop("password")
            )
            validated_data.pop("confirmed_password")
        except IntegrityError:
            raise exceptions.ValidationError(
                f"This username is already existed: {username}"
            )

        return Organization.objects.create(user=user, **validated_data)

    class Meta:
        model = Organization
        exclude = ["user", "created_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Organization
        exclude = ["created_at"]
