from django.contrib import admin

from . import models

admin.site.register(models.Organization)
admin.site.register(models.Donator)
admin.site.register(models.RequiredItem)
admin.site.register(models.Donation)
