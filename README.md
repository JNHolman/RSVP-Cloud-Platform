# RSVP Cloud Platform

**A real business decision that turned into a larger cloud engineering project.**

This project actually started with [RSVP Society](https://github.com/JNHolman/rsvp-society), the event platform I built for my business. I needed a reliable way to manage members, invitations, RSVPs, guest lists, text messages, and check-in without doing everything manually.

That led to a bigger question: **How should I run the system without spending more on technology than the business needs?**

## How I ended up here

My first approach was to move RSVP Society to AWS using a fairly traditional setup: servers, load balancers, private networks, a relational database, backup systems, and layers of monitoring and security.

The design made technical sense. But as I kept building, I realized I was creating a Mack truck for a business that didn't need one.

RSVP Society isn't getting constant traffic all day, every day. Activity picks up when invitations go out, when people respond, and when events are happening. Paying for several servers and networking components to sit there around the clock wasn't a smart business decision.

**Just because I could build it didn't mean the business should pay for it.**

So I changed course.

RSVP Society now uses a lighter, event-driven AWS design. Services such as Lambda, DynamoDB, API Gateway, and EventBridge do work when there's actually work to do. CloudFront handles delivery. Jade, the text assistant, helps with guest conversations, while the application itself enforces the rules around membership, invitations, capacity, and attendance.

I didn't make the business less capable. I removed infrastructure that wasn't helping it.

I also didn't want to throw away the engineering behind that first design. It still had value—just not as the right solution for RSVP Society.

**That's why I kept building RSVP Cloud Platform separately.**

## What RSVP Cloud Platform became

The goal here is different from the goal of RSVP Society.

RSVP Society shows how I built a real business application and made practical decisions about what it needs.

RSVP Cloud Platform shows how I would engineer and operate a **larger AWS environment when the requirements actually justify it**.

I took the original infrastructure idea and developed it in three stages. It's one application and operating model that becomes more capable as the engineering requirements grow.

| Stage | In everyday terms | What I built |
| --- | --- | --- |
| **1. Build the foundation** | Get an application online, protect it, and make sure its data can be recovered. | Private AWS servers, a database, secure networking, monitoring, backups, and incident analysis |
| **2. Modernize it** | Make updates easier to release and recover when something goes wrong. | The same application running in containers, with automated testing, deployment, scaling, and rollback |
| **3. Operate it at scale** | Think about how teams keep a larger environment secure, accountable, and affordable. | Central security, access controls, audit records, cost analysis, and AI-assisted operations |

### Stage 1 — Build the foundation

I started with the traditional application setup that first made me consider AWS for RSVP Society.

The application runs on private EC2 servers behind a secure public entry point. It reads and writes test data in an encrypted MySQL database. The environment runs across two AWS Availability Zones so it doesn't depend on one location.

I added monitoring, alerts, backups, and recovery procedures because getting a website to load is only part of running a system. You also need to know when it breaks and how to get it back.

The incident workflow collects relevant alarm and log information and uses AI to help explain what happened. It stores the findings for review. **The AI advises; it doesn't make infrastructure changes.**

### Stage 2 — Modernize the same application

Next, I took the application from Stage 1 and made it run in containers rather than managing the application directly on EC2 servers.

That let me focus on something every engineering team deals with: **how to release changes without taking down a working service**.

GitHub Actions tests the code, scans the container, and sends a versioned release to AWS. ECS runs the application, checks its health, adjusts capacity when demand changes, and can return to a working version if a release fails.

The application behavior stays consistent. What changes is how I package, deploy, and operate it.

I don't need to keep both versions running permanently to demonstrate that progression. The test environments can be brought up, validated, and shut down.

### Stage 3 — Add the operational controls

Once an application is running and being updated regularly, the questions change.

Who has access? Where do security alerts go? How do you investigate an incident? Who can see audit records? And how do you keep an eye on the AWS bill?

This stage develops those capabilities through a multi-account AWS design, centralized security and logging, identity controls, cost analysis, and AI-assisted investigation.

I modeled the larger enterprise setup and tested its policies and analysis code locally. There's no reason to keep six AWS accounts running just to show how those responsibilities should be separated.

## The engineering behind it

A few things matter more to me than the number of services in the architecture.

**Protect the traffic.** The servers and database stay private. Customers reach the application through HTTPS and a web firewall, not by connecting directly to internal systems.

**Know what changed.** Infrastructure is defined with Terraform. Application versions can be traced to a Git commit, and GitHub Actions handles releases without storing permanent AWS deployment keys.

**Prove recovery works.** I tested restoring database data and recovering from a broken container release. A backup or rollback setting doesn't mean much until you've exercised it.

**Make problems easier to investigate.** Logs, alarms, and AI-assisted summaries help an engineer understand what's happening. They don't replace judgment or automatically change the environment.

**Pay attention to the bill.** Some enterprise controls cost real money even when nobody is using the application. I use controlled test windows, keep only the evidence and recovery assets I need, and shut down temporary workloads afterward.

## What the AWS tests showed

The earlier live exercises established that the foundation could serve traffic privately across two Availability Zones, that the web firewall blocked a test request, and that an encrypted database snapshot could be restored with its data intact.

That database restore took **10 minutes and 2 seconds**, measured from the restore request to successfully reading the test record.

On the container side, I used GitHub Actions to release an application to private ECS tasks. I also deliberately deployed a broken revision. ECS restored the previous healthy version in **13 minutes and 47 seconds**.

Those are measured results, not estimates. The dated reports preserve the exact test conditions and engineering problems encountered along the way. The shared-application integration and additional automation checks are covered by the project's final test plan and code-level validation.

[Project 1 test record](docs/PROJECT-1-LIVE-2026-11-08.md) · [Project 2 test record](docs/PROJECT-2-LIVE-2026-11-08.md) · [Validation details](docs/PORTFOLIO-VALIDATION.md)

## The trade-off is the point

| RSVP Society — the actual business | RSVP Cloud Platform — the engineering project |
| --- | --- |
| Traffic comes in bursts around events. | Models an environment with larger reliability and operational needs. |
| Use services that run when needed. | Explore private servers, containers, managed databases, and multi-zone infrastructure. |
| Keep ongoing costs and maintenance practical. | Demonstrate how to build, automate, secure, troubleshoot, and recover a more complex platform. |
| Put the complexity into event rules and guest experience. | Put the engineering depth into infrastructure, delivery, security, and operations. |

Neither architecture is automatically better. **The right one depends on what the business is trying to accomplish.**

I came into this with a background in enterprise networking—troubleshooting outages, understanding traffic paths, managing changes, and restoring service. I wanted to apply that same mindset to cloud engineering.

The biggest lesson from the whole project isn't that I learned how to configure more AWS services.

It's that **good engineering includes knowing when not to use them.**

## Take a closer look

- [How the platform is designed](docs/ARCHITECTURE.md) — the three stages, how they fit together, and the decisions behind them.
- [Testing and evidence](docs/PORTFOLIO-VALIDATION.md) — what the AWS exercises demonstrated and how the remaining checks are organized.
- [Deployment and recovery guide](docs/DEPLOYMENT.md) — the technical procedures and safety controls.
- [Infrastructure code](infrastructure/) — Terraform, workloads, and governance.
- [GitHub workflows](.github/workflows/) — tests, security checks, and application deployment.

---

**Josh Holman**  
Network / Cloud Infrastructure Engineer
