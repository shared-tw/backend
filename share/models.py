from django.contrib.auth import get_user_model
from django.db import models

from .choices import Cities, ContactMethods, OrganizationTypes, Units

User = get_user_model()


class Organization(models.Model):
    type = models.CharField(max_length=16, choices=OrganizationTypes.choices)
    type_other = models.CharField(max_length=20)
    name = models.CharField(max_length=32)
    city = models.CharField(max_length=16, choices=Cities.choices)
    address = models.CharField(max_length=128)
    phone = models.CharField(max_length=15)
    office_hours = models.CharField(max_length=128)
    other_contact_method = models.CharField(
        max_length=16, choices=ContactMethods.choices
    )
    other_contact = models.CharField(max_length=128)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Donator(models.Model):
    phone = models.CharField(max_length=15)
    other_contact_method = models.CharField(
        max_length=16, choices=ContactMethods.choices
    )
    other_contact = models.CharField(max_length=128)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class RequiredItem(models.Model):
    name = models.CharField(max_length=256)
    amount = models.PositiveSmallIntegerField()
    unit = models.CharField(max_length=16, choices=Units.choices)
    ended_date = models.DateField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ended_date"]
