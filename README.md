# RSVP Cloud Platform

**I built an AWS environment that investigates service failures, rejects bad releases and preserves the evidence behind a security alert.** I used the same read-only reservation service to test how much of that work could be automated and where an engineer still had to make the decision.

When RSVP Society sends a wave of invitations, guests reply, change plans and bring friends. Between events there may be very little work for the application to do. My first AWS design kept application servers and a highly available database running throughout those quiet periods. For the business, it made more sense to pay for work as requests arrived. I moved the production application toward event-driven services. [RSVP Society and its event operations](https://github.com/JNHolman/rsvp-society)

I kept the original design to answer a different question from my work in network operations: when a customer request fails, can I follow it from the public entry point to the database, find what broke, and prove that service has recovered? **RSVP Cloud Platform is the environment I built to test that question.** I ran the same read-only application on virtual machines and containers, deliberately introduced failures, and kept the results after retiring the temporary infrastructure.

## One application, two ways to serve it

```mermaid
flowchart TB
  user["Client · HTTPS"] --> f["Foundation load balancer"]
  user --> d["Delivery load balancer"]
  subgraph foundation["Foundation network"]
    f --> vm["Private application servers"]
    vm --> db[("Reservation database")]
  end
  subgraph delivery["Delivery network"]
    d --> tasks["Private container tasks"]
  end
  tasks -->|Private peering · authenticated database reads| db
```

Both paths could return the same reservation. That gave me a concrete way to test a network route, a software release and a restored database: could the application still read the expected data? The governance layer extends that work to the people and policies responsible for investigating problems. Its live exercise tested who gets the final say when an AI recommendation conflicts with security policy.

## What happened when I exercised the controls

| Operator’s question | What the automation did | What I verified |
|---|---|---|
| [Why did the service return errors?](project-1-cloud-foundation/README.md#ai-incident-analysis) | A controlled alarm triggered a Python investigation of 77 application log entries. | The model traced earlier 503 responses to refused backend connections and identified when health checks recovered. A subscriber received the report reference. |
| [Is the right release serving customers?](project-2-ecs-cicd/README.md#live-integrated-release-on-november-8) | GitHub Actions checked the version returned over HTTPS, rejected a healthy but incorrect revision, and restored its predecessor. | The previous release was verified in **3m 23s**. In a separate unhealthy-task drill, ECS recovered in **13m 47s**. |
| [Who sets the priority of a critical finding?](project-3-cloud-governance/README.md#live-aws-exercise) | A labeled sample triggered AI triage. The model proposed P3; the handler enforced the critical severity floor of P1. | Both decisions were preserved and the alert reached an encrypted subscriber. AWS also validated the service control policy documents. Policy logic has offline coverage. Cross-account enforcement remains unverified. |

Recovery required a different test. I restored an encrypted database snapshot and queried a known reservation. The row was readable in **10m 02s**. During a separate load exercise the container service grew from two running tasks to three. The project pages include the [database timelines](project-1-cloud-foundation/README.md#recovery-evidence) and [recorded task counts](project-2-ecs-cicd/README.md#capacity-under-load).

## Engineering Decisions and Trade-offs

**Production isolation.** The lab shared an AWS account with Society. Dedicated resource names, Terraform state keys and a delegated DNS zone under `cloud.rsvpsociety.com` bounded the exercise. Reviewed plans excluded Society’s database, IAM identities and production DNS. An older development resource with unclear ownership was left alone.

**Release ownership.** Foundation owned the database and private network. Delivery owned the peering connection, return routes and reader permissions. Separate state let me retire the consumer first. Terraform managed the infrastructure baseline, while GitHub Actions promoted application revisions. In the governance design, AWS Config aggregation covers accounts only where Config recording is enabled.

**Recovery and cost.** Terraform retired 80 foundation resources, 60 ECS runtime resources and two temporary delivery resources. Release task definitions 6 and 7 remained registered after service retirement. The final RDS snapshot was available and encrypted. RDS recovery points inherit the database encryption key. Project 1 recovery KMS keys have intentional Terraform destruction guards, so I do not expect an unrestricted `terraform destroy` to remove them alongside the runtime.

The encrypted snapshots, completed AWS Backup recovery point, log buckets and incident index were retained. Keys and storage can continue to incur charges. No cost-allocation tags were active during the exercise, so the portfolio’s share of the bill could not be established.

The infrastructure scan is advisory. The review covers IAM scope, reachability, encryption and monitoring across the three layers. [Disposition of the 42 Checkov findings](shared/checkov-review.md)

**Josh Holman** — Network / Cloud Infrastructure Engineer
