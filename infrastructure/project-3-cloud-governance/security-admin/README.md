# RSVP Delegated Security Administration

Run this stack in the member account designated by the management-account `organization` stack as the GuardDuty and Security Hub administrator.

It enables:

- GuardDuty in the delegated security account
- automatic GuardDuty enrollment for organization members
- Security Hub in the delegated security account
- automatic Security Hub enrollment for organization members
- organization-wide AWS Config aggregation for accounts/Regions that already have Config recorders enabled

The organization bootstrap must be applied first so trusted access and delegated administration already exist.

This stack deliberately does **not** pretend that an aggregator enables AWS Config recording in member accounts. Member-account recorders/delivery channels must exist (for example through an account baseline or service-managed StackSet) before those accounts produce Config data for the aggregator.
