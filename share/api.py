import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from ninja import Router, errors

from . import models, pagination, schemas

logger = logging.getLogger(__name__)
public_router = Router(tags=["Public"])
organization_router = Router(tags=["Organization"])
register_rotuer = Router(tags=["Register"])

User = get_user_model()


def create_user(username: str, password: str, confirmed_password: str, user, assoc_cls):
    if password != confirmed_password:
        raise ValueError("Password is not matched.")
    elif len(password) < 8:
        raise ValueError("The length of password should be greater than 8 characters.")
    elif username.startswith("_"):
        raise ValueError(422, "Username cannot start with underscore (_).")

    try:
        django_validate_password(password, user)
        user = User.objects.create_user(username=username, password=password)

    except IntegrityError:
        raise ValueError(f"Username is already existed: {username}")
    except ValidationError as e:
        raise errors.HttpError(422, f"Password validation failed: {e}")


@register_rotuer.post("/organization", response=schemas.Organization)
def create_organization(request, payload: schemas.OrganizationCreation):
    try:
        if not request.user.is_active and request.auth.get("new_user", False):
            # TODO: send activation mail
            request.user.email = payload.email
            request.user.is_active = True
            request.user.save()
        data = payload.dict(
            exclude={"username", "password", "confirmed_password", "email"}
        )

        return models.Organization.objects.create(user=request.user, **data)
    except IntegrityError:
        raise errors.HttpError(
            422, f'User is already associated with "{request.user.organization.name}".'
        )
    except ValidationError as e:
        raise errors.HttpError(422, f"Unable to create user: {e}")


@register_rotuer.post("/donator", response=schemas.Donator)
def create_donator(request, payload: schemas.DonatorCreation):
    try:
        if not request.user.is_active and request.auth.get("new_user", False):
            # TODO: send activation mail
            request.user.email = payload.email
            request.user.is_active = True
            request.user.save()
        data = payload.dict(
            exclude={"username", "password", "confirmed_password", "email"}
        )

        return models.Donator.objects.create(user=request.user, **data)
    except IntegrityError:
        raise errors.HttpError(
            422, f'User is already associated with "{request.user.donator.name}".'
        )
    except ValidationError as e:
        raise errors.HttpError(422, f"Unable to create user: {e}")


@public_router.get(
    "/required-items",
    response=pagination.PaginatedResponseSchema[schemas.GroupedRequiredItems],
)
def list_required_items(request, page: int = 1):
    items = models.RequiredItem.objects.all()
    grouped_items = {}
    for i in items:
        g = grouped_items.setdefault(
            i.organization.id, schemas.GroupedRequiredItems(organization=i.organization)
        )
        g.items.append(i)
    return pagination.render(
        request,
        items=list(grouped_items.values()),
        schema_cls=schemas.GroupedRequiredItems,
        page=page,
    )


@organization_router.get(
    "/required-items",
    response=pagination.PaginatedResponseSchema[schemas.RequiredItem],
)
def list_organization_required_items(request, page: int = 1):
    items = models.RequiredItem.objects.filter(organization__user=request.user)
    return pagination.render(
        request, items=items, schema_cls=schemas.RequiredItem, page=page
    )


@organization_router.post("/required-items", response=schemas.RequiredItem)
def create_organization_required_item(request, payload: schemas.RequiredItemCreation):
    return models.RequiredItem.objects.create(
        organization=request.user.organization, **payload.dict()
    )
