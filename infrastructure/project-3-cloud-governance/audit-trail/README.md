# RSVP Organization Audit Trail

Run this stack in the Organizations management account **after** the Log Archive stack. Supply the Log Archive bucket name and KMS key ARN as inputs.

The resulting CloudTrail is organization-wide, multi-Region, encrypted, log-file validated, and writes to the dedicated Log Archive account.
