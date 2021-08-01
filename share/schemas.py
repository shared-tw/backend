import datetime
import typing
from datetime import date
from typing import List, Optional

from ninja import Field, Schema
from pydantic import EmailStr

from share import choices, states


class OrganizationSummary(Schema):
    id: int
    type: str
    name: str
    city: choices.Cities


class DonationCreation(Schema):
    id: int
    amount: int
    excepted_delivery_date: Optional[datetime.date]


class DonationModification(Schema):
    id: int = 0
    name: states.EventEnum = Field(..., alias="event")
    comment: str = ""


class Donation(Schema):
    id: int
    required_item: str = Field(..., alias="required_item_name")
    amount: int
    state: states.DonationStateEnum
    created_at: datetime.datetime
    modified_at: datetime.datetime


class RequiredItemBase(Schema):
    name: str
    amount: int
    unit: choices.Units
    ended_date: date


class RequiredItemCreation(RequiredItemBase):
    pass


class RequiredItem(RequiredItemBase):
    id: str
    state: states.RequiredItemStateEnum
    approved_amount: int
    delivered_amount: int
    donations: typing.List[Donation]


class GroupedRequiredItems(Schema):
    organization: OrganizationSummary
    items: List[RequiredItem] = []


class OrganizationBase(Schema):
    name: str
    type: choices.OrganizationTypes
    type_other: str
    city: choices.Cities
    address: str
    phone: str
    office_hours: str
    other_contact_method: choices.ContactMethods
    other_contact: str


class Organization(OrganizationBase):
    id: int


class OrganizationCreation(OrganizationBase):
    username: str
    password: str
    confirmed_password: str
    email: EmailStr


class DonatorBase(Schema):
    phone: str
    other_contact_method: choices.ContactMethods
    other_contact: str


class DonatorCreation(DonatorBase):
    email: EmailStr


class Donator(DonatorBase):
    id: int


class SetDonationResult(Schema):
    message: typing.Optional[str] = None
    donation: typing.Optional[Donation] = None


class UserMe(Schema):
    name: str
    email: str = ""
    phone: str = ""
    other_contact_method: str = ""
    other_contact: str = ""
