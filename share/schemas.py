from datetime import date

from ninja import Schema

from share import choices


class OrganizationSummary(Schema):
    type: str
    name: str
    city: choices.Cities


class RequiredItemBase(Schema):
    name: str
    amount: int
    unit: choices.Units
    ended_date: date


class RequiredItemCreation(RequiredItemBase):
    pass


class RequiredItem(RequiredItemBase):
    id: str
    organization: OrganizationSummary


class UserCreationMixIn(Schema):
    username: str
    password: str
    confirmed_password: str


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


class OrganizationCreation(OrganizationBase, UserCreationMixIn):
    pass


class DonatorBase(Schema):
    phone: str
    other_contact_method: choices.ContactMethods
    other_contact: str


class DonatorCreation(DonatorBase, UserCreationMixIn):
    pass


class Donator(DonatorBase):
    id: int
