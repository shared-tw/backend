from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from rest_framework import exceptions, serializers

from .models import Donator, Organization, RequiredItem

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username"]


class CreateUserMixIn(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    confirmed_password = serializers.CharField()

    def create_user(self, validated_data):
        if validated_data["password"] != validated_data["confirmed_password"]:
            raise exceptions.ValidationError("Password doesn't match.")

        username = validated_data.pop("username")
        try:
            validated_data.pop("confirmed_password")
            return (
                User.objects.create_user(
                    username=username, password=validated_data.pop("password")
                ),
                validated_data,
            )
        except IntegrityError:
            raise exceptions.ValidationError(
                f"This username is already existed: {username}"
            )


class CreateOrganizationSerializer(serializers.ModelSerializer, CreateUserMixIn):
    name = serializers.CharField()

    def create(self, validated_data):
        user, validated_data = self.create_user(validated_data)
        return Organization.objects.create(user=user, **validated_data)

    class Meta:
        model = Organization
        exclude = ["user", "created_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Organization
        exclude = ["created_at"]


class CreateDonatorSerializer(serializers.ModelSerializer, CreateUserMixIn):
    def create(self, validated_data):
        user, validated_data = self.create_user(validated_data)
        return Donator.objects.create(user=user, **validated_data)

    class Meta:
        model = Donator
        exclude = ["user", "created_at"]


class DonatorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Donator
        exclude = ["user", "created_at"]


class OrganizationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["type", "name", "city"]
        read_only_fields = ["type", "name", "city"]


class RequiredItemSerializer(serializers.ModelSerializer):
    organization = OrganizationSummarySerializer(read_only=True)

    class Meta:
        model = RequiredItem
        exclude = ["created_at"]
