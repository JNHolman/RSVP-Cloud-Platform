# Testing and evidence

I don't want this project to be a diagram with a long list of AWS services. The useful question is whether the system does what it says it does.

This page keeps the evidence organized. The [main README](../README.md) explains the business decision and overall project. The [architecture guide](ARCHITECTURE.md) explains the design.

## The original live AWS exercises — November 8, 2026

These are the **measured results from the original deployment sessions**. They stay attached to the date and version tested, even when the code changes later.

| What I tested | What happened | Evidence |
| --- | --- | --- |
| Private application servers | Two healthy EC2 instances served the test page from different Availability Zones, without public IP addresses | [Project 1 exercise](PROJECT-1-LIVE-2026-11-08.md) |
| Secure web traffic | HTTPS returned a healthy response; WAF blocked a harmless simulated attack | [Project 1 exercise](PROJECT-1-LIVE-2026-11-08.md) |
| Database recovery | A known record survived a restore to a separate encrypted RDS database. Request to verified read: **10m 02s** | [Project 1 recovery timeline](PROJECT-1-LIVE-2026-11-08.md#recovery-timeline) |
| Monitoring | CloudWatch recorded an unhealthy-target alarm entering and leaving the alarm state | [Project 1 observations](evidence/project-1-2026-11-08/observations.json) |
| AI handler and persistence | A direct Lambda test produced a stored, encrypted fallback report; a separate local handler test exercised a live model response | [Project 1 exercise](PROJECT-1-LIVE-2026-11-08.md) |
| Automated container deployment | GitHub Actions authenticated through OIDC, built and scanned an image, then deployed it to private ECS tasks | [Project 2 exercise](PROJECT-2-LIVE-2026-11-08.md) |
| Failed release recovery | A deliberately broken ECS revision recovered to the previous healthy version in **13m 47s** | [Project 2 exercise](PROJECT-2-LIVE-2026-11-08.md) |
| Container security review | A newer image reduced ECR's HIGH findings from nine to two, with no CRITICAL findings in either image scan | [Project 2 scan comparison](evidence/project-2-2026-11-08/image-rescan.json) |
| Enterprise governance | Terraform and Python tests exercised policies, security analysis, fallback responses, and reporting without deploying six accounts | [Offline test guide](DEPLOYMENT.md#project-3-offline-validation) |

The original exercises also uncovered actual problems: an AWS Lambda concurrency limit, a KMS permission issue, a container temporary-file failure, and container package vulnerabilities. The dated reports show those failures and how they were handled. That troubleshooting is part of the project, not something to hide.

## Final integration and automation checks

The finished engineering work uses **one application contract across EC2 and ECS**. Its validation covers:

| Area | What the check demonstrates |
| --- | --- |
| Application and database | The same app can run in both hosting models and read/write synthetic MySQL data |
| AI incident handling | A matching alarm is routed to the handler, evidence is bounded and checked, and encrypted analysis results are saved and sent to an operator |
| Backup and recovery | AWS Backup, point-in-time recovery, and controlled database failover have a repeatable procedure with data checks and timing |
| GitHub deployment rollback | The release workflow can detect a failed smoke test and restore a healthy revision independently of ECS-native rollback |
| Scaling | A bounded test can drive ECS above its minimum task count and back down |
| Container security | Images are rebuilt and scanned; outstanding vendor findings are tracked rather than ignored |
| CI controls | Mandatory test gates fail when required checks fail; advisory checks are identified clearly |
| Governance | Terraform and local runtime tests validate enterprise policy and operations behavior without maintaining multiple AWS accounts |

**Test procedures and automated checks are different from a recorded live result.** The dated reports above remain the source for measured AWS outcomes. New live results should be added as new dated evidence rather than changing history.

## What this cost

The original workload budget estimates were approximately **$0.72/hour** for the Project 1 stack and **$0.18/hour** for Project 2, before variable usage, extra recovery resources, and retained storage.

Those were planning estimates, **not actual billed totals**. The original combined validation spending target was **$75**. Because the account also contains RSVP Society production usage, whole-account billing totals cannot be treated as the Cloud Platform bill.

The temporary demo workloads were shut down after testing. Retained snapshots, encryption keys, logs, ECR images, state storage, and DNS can continue to cost money.

The same cost lesson that led me to simplify RSVP Society applies here: **I don't need to pay for a large environment every day just to prove I know how to build one.**

## Where the technical details live

- [Architecture and engineering decisions](ARCHITECTURE.md)
- [Project 1 live report, November 8](PROJECT-1-LIVE-2026-11-08.md)
- [Project 1 raw observations](evidence/project-1-2026-11-08/observations.json)
- [Project 2 live report, November 8](PROJECT-2-LIVE-2026-11-08.md)
- [Project 2 raw observations](evidence/project-2-2026-11-08/observations.json)
- [Project 2 image scan comparison](evidence/project-2-2026-11-08/image-rescan.json)
- [Deployment, test commands, and cleanup rules](DEPLOYMENT.md)
- [GitHub Actions workflows](../.github/workflows/)

The implementation and its automated tests are in the repository. Live evidence stays tied to the exact version, conditions, and date observed.
