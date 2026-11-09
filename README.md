# RSVP Cloud Platform

**I built an AWS environment that investigates service failures, rejects bad releases and preserves the evidence behind a security alert.** I used the same read-only reservation service to test how much of that work could be automated and where an engineer still had to make the decision.

When RSVP Society sends a wave of invitations, guests reply, change plans and bring friends. Between events there may be very little work for the application to do. My first AWS design kept application servers and a highly available database running throughout those quiet periods. For the business, it made more sense to pay for work as requests arrived. I moved the production application toward event-driven services. [RSVP Society and its event operations](https://github.com/JNHolman/rsvp-society)

I kept the original design to answer a question from my work in network operations: when a request fails, can I follow it from the public entry point to the database and prove when service recovers?

I used Terraform to build private AWS networks around two ways to serve the same application: EC2 virtual machines and ECS Fargate containers reading from an RDS database. GitHub Actions automated the build, security scan, deployment and recovery of container releases. When a CloudWatch alarm changed state, a Python function in Lambda collected evidence for an AI-assisted investigation. The governance design separates who can deploy a workload from who can administer security policy. In the live security exercise, an explicit priority rule controlled the alert after AI triage.

## From a failed request to an operating decision

```mermaid
flowchart TB
  subgraph runtime["One application · two private networks"]
    vm["Foundation · EC2 servers"] -->|Read| db[("Private RDS database")]
    tasks["Delivery · ECS containers"] -->|Read over peering| db
  end
  vm -. Alarm and logs .-> investigate["Investigate · 77 log entries informed an advisory report"]
  tasks -. Serving version .-> recover["Recover · wrong release rolled back in 3m 23s"]
  sample["Governance · separate single-account exercise"] -->|Labeled critical finding| decide["Escalate · policy enforced P1 despite the model’s P3"]
  classDef outcome fill:#e7f4ee,color:#173a2b,stroke:#47785c
  class investigate,recover,decide outcome
```

Both paths could return the same reservation. That gave me a concrete way to test a network route, a software release and a restored database: could the application still read the expected data? The governance layer extends that work to the people and policies responsible for investigating problems. Its live exercise tested who gets the final say when an AI recommendation conflicts with security policy.

## What happened when I exercised the controls

| Operator’s question | What the automation did | What I verified |
|---|---|---|
| [Why did the service return errors?](project-1-cloud-foundation/README.md#ai-incident-analysis) | A controlled alarm triggered a Python investigation of 77 application log entries. | Logs showed 503s followed by successful health checks. The model identified refused backend connections as the likely explanation for the earlier errors. A subscriber received the report reference. |
| [Is the right release serving customers?](project-2-ecs-cicd/README.md#live-integrated-release-on-november-8) | GitHub Actions checked the version returned over HTTPS, rejected a healthy but incorrect revision, and restored its predecessor. | The previous release was verified in **3m 23s**. In a separate unhealthy-task drill, ECS recovered in **13m 47s**. |
| [Who sets the priority of a critical finding?](project-3-cloud-governance/README.md#live-aws-exercise) | A labeled sample triggered AI triage. The model proposed P3; the handler enforced the critical severity floor of P1. | Both decisions were preserved and the alert reached an encrypted subscriber. AWS also validated the service control policy documents. Policy logic has offline coverage. Cross-account enforcement remains unverified. |

Recovery required a different test. I restored an encrypted database snapshot and queried a known reservation. The row was readable in **10m 02s**. During a separate load exercise the container service grew from two running tasks to three. The project pages include the [database timelines](project-1-cloud-foundation/README.md#recovery-evidence) and [recorded task counts](project-2-ecs-cicd/README.md#capacity-under-load).

## Engineering Decisions and Trade-offs

**Production isolation.** The lab shared an AWS account with Society. Dedicated resource names, Terraform state keys and a delegated DNS zone under `cloud.rsvpsociety.com` bounded the exercise. Reviewed plans excluded Society’s database, IAM identities and production DNS. An older development resource with unclear ownership was left alone.

**Release ownership.** Foundation owned the database and private network. Delivery owned the peering connection, return routes and reader permissions. Separate state let me retire the consumer first. Terraform managed the infrastructure baseline, while GitHub Actions promoted application revisions. In the governance design, AWS Config aggregation covers accounts only where Config recording is enabled.

<details>
<summary>Retired resources, continuing costs and security findings</summary>

**Recovery and cost.** Terraform retired 80 foundation resources, 60 ECS runtime resources and two temporary delivery resources. Release task definitions 6 and 7 remained registered after service retirement. The final RDS snapshot was available and encrypted. RDS recovery points inherit the database encryption key. Project 1 recovery KMS keys have intentional Terraform destruction guards, so I do not expect an unrestricted `terraform destroy` to remove them alongside the runtime.

The encrypted snapshots, completed AWS Backup recovery point, log buckets and incident index were retained. Keys and storage can continue to incur charges. No cost-allocation tags were active during the exercise, so the portfolio’s share of the bill could not be established.

The infrastructure scan is advisory. The review covers IAM scope, reachability, encryption and monitoring across the three layers. [Disposition of the 42 Checkov findings](shared/checkov-review.md)

</details>

For RSVP Society, the useful decision was knowing when the business could dispense with always-on servers. For the enterprise platform, the useful test was what an operator could establish during a failure. A release was back in service when the expected version answered over HTTPS. A backup was usable when a restored database returned the expected row. An AI investigation earned its place by giving the engineer a specific next check and enough evidence to judge the answer.

**Josh Holman** — Network / Cloud Infrastructure Engineer
