# Operating the portfolio beside RSVP Society

RSVP Society and the portfolio shared an AWS account. The exercises used dedicated resource names, state keys and a delegated DNS zone under `cloud.rsvpsociety.com`. The production application, its database and its parent DNS records were outside the reviewed plans. An older development resource with uncertain ownership was also left alone.

Foundation owned the database and private network. Delivery owned its VPC peering connection, return routes and reader permissions. Independent Terraform state let me retire the consumer before removing the foundation. GitHub Actions owned application releases so infrastructure changes could not silently replace a verified serving version.

The integrated exercise retired **80 foundation resources, 60 ECS runtime resources and two delivery resources**. Release task definitions 6 and 7 remained registered after the service was removed. The final RDS snapshot was available and encrypted. Recovery points depend on access to the original database key. For that reason I do not expect an unrestricted `terraform destroy` to remove the protected keys alongside the runtime.

The encrypted snapshots, completed AWS Backup recovery point, log buckets and incident index were retained. KMS keys and retained storage can continue to incur charges. No cost-allocation tags were active during the exercise, so account-wide billing cannot establish a portfolio-only total. [Database recovery evidence](../project-1-cloud-foundation/README.md#recovery-evidence) · [Single-account governance results](../project-3-cloud-governance/README.md#live-aws-exercise)
