import logging
import typing
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from ninja import Router, errors

from authenticator.api import JWTAuthBearer
from authenticator.utils import send_verification_email

from . import models, schemas

logger = logging.getLogger(__name__)
router = Router()

User = get_user_model()


def create_user(
    username: str, email: str, password: str, confirmed_password: str
) -> User:
    if password != confirmed_password:
        raise ValueError("Password is not matched.")
    elif len(password) < 8:
        raise ValueError("The length of password should be greater than 8 characters.")
    elif username.startswith("_"):
        raise ValueError("Username cannot start with underscore (_).")

    try:
        django_validate_password(password)
        # FIXME: make is_active=False by default
        return User.objects.create_user(
            username=username, password=password, email=email
        )
    except IntegrityError:
        raise ValueError(f"Username is already existed: {username}")
    except ValidationError as e:
        raise ValueError(str(e))


@router.post(
    "/registration/organization",
    auth=None,
    response=schemas.Organization,
    tags=["Registration"],
)
def create_organization(request, payload: schemas.OrganizationCreation):
    try:
        user = create_user(
            payload.username,
            payload.email,
            payload.password,
            payload.confirmed_password,
        )
        data = payload.dict(
            exclude={"username", "password", "confirmed_password", "email"}
        )

        org = models.Organization.objects.create(user=user, **data)
        send_verification_email(request, user)
        return org
    except IntegrityError:
        raise errors.HttpError(
            422, f'User is already associated with "{request.user.organization.name}".'
        )
    except ValueError as e:
        raise errors.HttpError(400, f"Unable to create user: {e}")


@router.post(
    "/registration/donator",
    auth=JWTAuthBearer(inactive_user_raise_403=False),
    response=schemas.Donator,
    tags=["Registration"],
)
def create_donator(request, payload: schemas.DonatorCreation):
    try:
        data = payload.dict(
            exclude={"username", "password", "confirmed_password", "email"}
        )

        request.user.email = payload.email
        request.user.save()
        donator, _ = models.Donator.objects.update_or_create(
            user=request.user, defaults=data
        )
        send_verification_email(request, request.user)
        return donator
    except IntegrityError:
        raise errors.HttpError(
            422, f'User is already associated with "{request.user.donator.name}".'
        )
    except ValidationError as e:
        raise errors.HttpError(422, f"Unable to create user: {e}")


@router.get(
    "/required-items",
    auth=None,
    response=typing.List[schemas.GroupedRequiredItems],
    tags=["Donator"],
)
def list_required_items(request):
    items = models.RequiredItem.objects.prefetch_related("donations").filter(
        ended_date__gte=date.today()
    )
    grouped_items = {}
    for i in items:
        g = grouped_items.setdefault(
            i.organization.id, schemas.GroupedRequiredItems(organization=i.organization)
        )
        g.items.append(i)
    return [i.dict() for i in grouped_items.values()]


@router.get(
    "/organization/required-items",
    response=typing.List[schemas.RequiredItem],
    tags=["Organization"],
)
def list_organization_required_items(request):
    items = models.RequiredItem.objects.filter(organization__user=request.user)
    return items


@router.post(
    "/organization/required-items", response=schemas.RequiredItem, tags=["Organization"]
)
def create_organization_required_item(request, payload: schemas.RequiredItemCreation):
    if hasattr(request.user, "organization"):
        return models.RequiredItem.objects.create(
            organization=request.user.organization, **payload.dict()
        )
    raise errors.HttpError(400, "Invalid request")


@router.delete(
    "/organization/required-items/{required_item_id}",
    response={204: None},
    tags=["Organization"],
)
def delete_organization_required_items(request, required_item_id: int):
    required_item = get_object_or_404(
        models.RequiredItem, id=required_item_id, organization__user=request.user
    )
    required_item.cancel(request.user, "User cancelled.")
    return 204, None


@router.patch(
    "/organization/donations/{donation_id}",
    response=schemas.Donation,
    tags=["Organization"],
)
def edit_organization_donation(
    request,
    donation_id: int,
    payload: schemas.DonationModification,
):
    donation = get_object_or_404(
        models.Donation,
        id=donation_id,
        required_item__organization=request.user.organization,
    )
    try:
        donation.set_event(request.user, payload.dict())
    except ValueError as e:
        raise errors.HttpError(422, f"fail to add new event, reason: {e}")

    return donation


@router.post(
    "/required-items/donations",
    response=typing.List[schemas.SetDonationResult],
    tags=["Donator"],
)
def create_donation(request, payload: typing.List[schemas.DonationCreation]):
    result = [None] * len(payload)
    for i, donation in enumerate(payload):
        try:
            required_item = models.RequiredItem.objects.get(id=donation.id)
        except models.RequiredItem.DoesNotExist:
            result[i] = schemas.SetDonationResult(
                message=f"Required item ID doesn't exist: {donation.id}"
            )
            continue
        if not required_item.is_valid():
            result[i] = schemas.SetDonationResult(
                message=f"This required item is no longer collecting: {donation.id}"
            )
            continue
        if donation.amount > required_item.amount:
            result[i] = schemas.SetDonationResult(
                message=f"The amount of donation is greater than required one: {donation.id}"
            )
            continue

        donation = models.Donation.objects.create(
            required_item=required_item,
            created_by=request.user,
            **donation.dict(
                exclude={
                    "id",
                }
            ),
        )
        result[i] = schemas.SetDonationResult(donation=donation)
    return result


@router.get("/donations", response=typing.List[schemas.Donation], tags=["Donator"])
def list_donations(request):
    return models.Donation.objects.select_related("required_item").filter(
        created_by=request.user
    )


@router.patch(
    "/donations",
    response=typing.List[schemas.SetDonationResult],
    tags=["Donator"],
)
def edit_donation(request, payload: typing.List[schemas.DonationModification]):
    result = [None] * len(payload)
    for i, mod in enumerate(payload):
        try:
            donation = models.Donation.objects.get(id=mod.id)
        except models.Donation.DoesNotExist:
            result[i] = schemas.SetDonationResult(
                message=f"Donation ID doesn't exist: {mod.id}"
            )
            continue

        try:
            donation.set_event(request.user, mod.dict())
            result[i] = schemas.SetDonationResult(donation=donation)
        except ValueError as e:
            result[i] = schemas.SetDonationResult(
                message=f"fail to add new event, reason: {e}"
            )
    return result


@router.get("/users/me", response=schemas.UserMe, tags=["User"])
def get_users_me(request):
    kwargs = {}
    if hasattr(request.user, "donator"):
        extra_info = request.user.donator
        kwargs["name"] = request.uset.get_full_name()
    elif hasattr(request.user, "organization"):
        extra_info = request.user.organization
        kwargs["name"] = extra_info.name
    else:
        extra_info = None

    if extra_info:
        kwargs.update(
            dict(
                phone=extra_info.phone,
                other_contact_method=extra_info.other_contact_method,
                other_contact=extra_info.other_contact,
            )
        )
    return schemas.UserMe(email=request.user.email, **kwargs)
