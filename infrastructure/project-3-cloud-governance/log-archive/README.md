# RSVP Log Archive Account

Run this stack while authenticated to the dedicated Log Archive member account.

It creates a private, versioned, KMS-encrypted S3 audit bucket with long-term lifecycle retention and a bucket/key policy that permits only the management account's named organization CloudTrail to deliver organization logs.
