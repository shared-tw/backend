import unittest

from . import states


class DonationStateTestCase(unittest.TestCase):
    def test_approve_pending_state(self):
        approve_pending_statue = states.PendingApprovalState()

        approved_event = states.DonationApprovedEvent()
        self.assertIsInstance(
            approve_pending_statue.apply(approved_event),
            states.PendingDispatchState,
        )

        cancelled_event = states.DonationCancelledEvent()
        self.assertIsInstance(
            approve_pending_statue.apply(cancelled_event), states.CancelledState
        )

        dispatch_event = states.DonationDispatchedEvent()
        self.assertIsInstance(
            approve_pending_statue.apply(dispatch_event), states.InvalidState
        )

    def test_dispatch_pending_state(self):
        dispatch_pending_state = states.PendingDispatchState()

        donation_dispatched_event = states.DonationDispatchedEvent()
        self.assertIsInstance(
            dispatch_pending_state.apply(donation_dispatched_event),
            states.DoneState,
        )

        cancelled_event = states.DonationCancelledEvent()
        self.assertIsInstance(
            dispatch_pending_state.apply(cancelled_event), states.CancelledState
        )

        approved_event = states.DonationApprovedEvent()
        self.assertIsInstance(
            dispatch_pending_state.apply(approved_event), states.InvalidState
        )

    def test_collect_pending_state(self):
        collect_pending_state = states.PendingDeliveryState()

        collected_event = states.DonationDeliveredEvent()
        self.assertIsInstance(
            collect_pending_state.apply(collected_event), states.DoneState
        )

        cancelled_event = states.DonationCancelledEvent()
        self.assertIsInstance(
            collect_pending_state.apply(cancelled_event), states.InvalidState
        )
