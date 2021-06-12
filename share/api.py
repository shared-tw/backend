import logging

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from ninja import Router, errors

from . import models, pagination, schemas

logger = logging.getLogger(__name__)
router = Router()

User = get_user_model()


@router.get(
    "/required-items/",
    auth=None,
    response=pagination.PaginatedResponseSchema[schemas.RequiredItem],
)
def list_required_items(request, page: int = 1):
    items = models.RequiredItem.objects.all()
    return pagination.render(
        request, items=items, schema_cls=schemas.RequiredItem, page=page
    )


@router.post("/register/organization/", auth=None, response=schemas.Organization)
def create_organization(request, organization: schemas.OrganizationCreation):
    if organization.password != organization.confirmed_password:
        raise errors.HttpError(422, "Password is not matched.")

    try:
        user = User.objects.create_user(
            username=organization.username, password=organization.password
        )
        data = organization.dict(exclude={"username", "password", "confirmed_password"})
        return models.Organization.objects.create(user=user, **data)
    except IntegrityError:
        raise errors.HttpError(422, "Username is already existed.")


@router.post("/register/donator/", auth=None, response=schemas.Donator)
def create_donator(request, donator: schemas.DonatorCreation):
    if donator.password != donator.confirmed_password:
        raise errors.HttpError(422, "Password is not matched.")

    try:
        user = User.objects.create_user(
            username=donator.username, password=donator.password
        )
        data = donator.dict(exclude={"username", "password", "confirmed_password"})
        return models.Donator.objects.create(user=user, **data)
    except IntegrityError:
        raise errors.HttpError(422, "Username is already existed.")


@router.get(
    "/organization-required-items/",
    response=pagination.PaginatedResponseSchema[schemas.RequiredItem],
)
def list_organization_required_items(request, page: int = 1):
    items = models.RequiredItem.objects.filter(organization__user=request.user)
    return pagination.render(
        request, items=items, schema_cls=schemas.RequiredItem, page=page
    )


@router.post("/organization-required-items/", response=schemas.RequiredItem)
def create_organization_required_item(request, payload: schemas.RequiredItemCreation):
    return models.RequiredItem.objects.create(
        organization=request.user.organization, **payload.dict()
    )
