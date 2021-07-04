import logging
import typing
from datetime import date, timedelta
from functools import singledispatchmethod

from django.contrib.auth import get_user_model
from django.db import OperationalError, models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import schemas, states
from .choices import Cities, ContactMethods, OrganizationTypes, Units

User = get_user_model()
logger = logging.getLogger(__name__)


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
    state = models.CharField(
        max_length=64,
        default=states.CollectingState.state_id(),
        choices=states.RequiredItemStateEnum.choices,
    )
    unit = models.CharField(max_length=16, choices=Units.choices)
    ended_date = models.DateField()
    # TODO: replace with created_by (User)?
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # TODO: add events?
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    @property
    def approved_amount(self):
        amount = 0
        for d in self.donations.all():
            if d.state in (
                states.PendingDispatchState.state_id(),
                states.DoneState.state_id(),
            ):
                amount += d.amount
        return amount

    @property
    def delivered_amount(self):
        amount = 0
        for d in self.donations.all():
            if d.state == states.DoneState.state_id():
                amount += d.amount
        return amount

    def cancel(self, user, comment: str):
        if not self.is_valid():
            return

        for d in self.donations.all():
            try:
                d.set_event(
                    user,
                    schemas.DonationModification(
                        event=states.DonationCancelledEvent.event_id(), comment=comment
                    ).dict(),
                )
            except ValueError:
                pass
        self.state = states.CancelledState.state_id()
        self.save()

    def is_valid(self) -> bool:
        if self.state == states.CollectingState.state_id():
            return True
        return False

    def calc_state(self):
        if not self.is_valid():
            return

        # TODO: lock?
        if self.ended_date < date.today():
            self.cancel(self.organization.user, "Over-due")
        if self.delivered_amount > self.amount:
            self.state = states.DoneState.state_id()
        self.save()

    class Meta:
        ordering = ["-ended_date"]


class Donation(models.Model):
    required_item = models.ForeignKey(
        RequiredItem, on_delete=models.CASCADE, related_name="donations"
    )
    amount = models.PositiveIntegerField()
    state = models.CharField(
        max_length=64,
        default=states.PendingApprovalState.state_id(),
        choices=states.DonationStateEnum.choices,
    )
    estimated_delivery_days = models.PositiveSmallIntegerField()
    excepted_delivery_date = models.DateField(null=True)
    events = models.JSONField(default=list)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    @property
    def required_item_name(self) -> str:
        return self.required_item.name

    @singledispatchmethod
    def perform_action(self, arg):
        raise NotImplementedError("Unknown action")

    @perform_action.register
    def _approval_action(self, action: states.ApprovalAction):
        self.excepted_delivery_date = date.today() + timedelta(
            days=self.estimated_delivery_days
        )

    def calc_state(self) -> states.State:
        current_state = states.get_state(self.state)
        for raw_event in self.events:
            e = states.get_event(raw_event)
            if e.timestamp < self.modified_at.timestamp():
                continue
            current_state, action = current_state.apply(e)
            if action is not None:
                self.perform_action(action)

        return current_state

    def set_event(self, user, raw_event: typing.Dict):
        try:
            event = states.get_event(raw_event)
            if not hasattr(user, "organization") and not hasattr(user, "donator"):
                raise ValueError("Invalid user account")
            elif hasattr(user, "organization") and not isinstance(
                event, states.organization_events
            ):
                raise ValueError(f"Invalid event of the organization: {event.name}")
            elif hasattr(user, "donator") and not isinstance(
                event, states.donator_events
            ):
                raise ValueError(f"Invalid event of the donator: {event.name}")
        except ValueError as e:
            raise e

        if self.state in (
            states.InvalidState.state_id(),
            states.CancelledState.state_id(),
        ):
            raise ValueError("This donation is already invalid or cancelled.")

        with transaction.atomic():
            try:
                donation = (
                    self.__class__.objects.filter(id=self.id)
                    .select_for_update(nowait=True)
                    .get()
                )
            except OperationalError:
                raise ValueError(f"Unable to lock the donation: {id}")

            donation.events.append(event.dict())
            new_state = donation.calc_state()
            if isinstance(new_state, states.InvalidState):
                raise ValueError("An invalid state has been generated.")
            donation.state = new_state.state_id()
            donation.save()


@receiver(post_save, sender=Donation)
def refresh_required_item(sender, instance, **kwargs):
    instance.required_item.calc_state()
