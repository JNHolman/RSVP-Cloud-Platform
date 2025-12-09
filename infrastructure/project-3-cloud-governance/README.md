# Project 3 – Multi-Account Security, Governance & AI Incident Response (Enterprise Layer)

Project 3 takes the RSVP platform from “working in one account” to **enterprise-grade governance** using multiple AWS accounts, centralized security services, cost controls, and an AI-assisted incident response workflow.

---

## Overview

This project uses **Terraform** to define:

- An AWS Organization with multiple accounts (e.g., Security, Dev, Prod)
- Service Control Policies (SCPs) as guardrails
- IAM Identity Center (SSO + permission sets)
- Centralized enablement of GuardDuty, Security Hub, and IAM Access Analyzer
- AWS Budgets and Cost Anomaly Detection
- An AI Incident Assistant:  
  - Ingests GuardDuty/CloudWatch events  
  - Processes them through an LLM  
  - Produces human-readable incident summaries (what happened, impact, next steps)

This is the “enterprise layer” that many companies layer on top of their workloads.

Live Service URL: http://rsvp-cloud-governance-dashboard.s3-website-us-east-1.amazonaws.com/

---

## Business Problem

As RSVP Society grows (or any SaaS/events platform grows), they face questions like:

- How do we **separate environments** cleanly (dev vs prod)?  
- How do we **keep security consistent** across accounts?  
- How do we **prevent dangerous actions** (e.g., disabling CloudTrail, making buckets public)?  
- How do we **control costs** as more teams deploy things?  
- How do we **respond quickly** when security findings come in?

Single-account setups don’t scale for this. Project 3 answers:  
“How would a Cloud Engineer introduce structure, guardrails, and intelligence?”

---

## Architecture Decisions

Key design choices:

- **Organizations + multiple accounts** instead of everything in one account  
- **Security services centralized** where appropriate  
- **SCPs for guardrails** instead of relying only on IAM  
- **IAM Identity Center** for proper SSO and permission sets  
- **Budgets + anomaly detection** as safeguards for cost  
- **AI assistant** to reduce time spent deciphering raw findings  

This aligns with modern AWS best practices for mid-sized teams.

---

## Architecture Breakdown

### AWS Organization & Accounts

- Organization root  
- Dedicated accounts such as:
  - **Security** (central guardrails, logging, security tools)
  - **Dev** (experimentation, non-critical workloads)
  - **Prod** (production RSVP workloads)  

### Guardrails (SCPs)

Examples of policy goals (tuned in Terraform code):

- Prevent disabling critical security services  
- Limit creation of internet-exposed resources without specific conditions  
- Restrict actions that would bypass governance (e.g., leaving the organization)  

SCPs don’t replace IAM but set **hard boundaries** for all accounts.

### Identity & Access

- IAM Identity Center as the SSO entry point  
- Permission sets for:
  - Cloud Engineer / Platform Engineer role  
  - Read-only / auditor roles  
  - Security operations roles  

This creates a consistent, auditable access model.

### Centralized Security Services

- **GuardDuty** enabled across accounts, sending findings to a central Security account  
- **Security Hub** aggregates security findings  
- **IAM Access Analyzer** for detecting risky resource policies  

These services provide visibility into misconfigurations and potential threats.

### Cost Governance

- AWS **Budgets** configured for accounts or services  
- **Cost Anomaly Detection** to flag unexpected spend increases  

This supports the business goal: “grow RSVP without financial surprises.”

### AI Incident Assistant

1. GuardDuty or CloudWatch events are generated (e.g., unusual API calls, public S3 bucket).
2. Events are routed (via EventBridge / CloudWatch → SNS) to a Lambda function.
3. Lambda collects relevant context and sends it to an LLM.
4. The LLM returns an **incident summary**:
   - What triggered the alert  
   - Likely impact  
   - Risk level  
   - Recommended next steps  
5. Summary is stored in S3 / DynamoDB and can be forwarded to email/Slack.

This turns streams of raw findings into **actionable, human-readable insights**.

---

## Cost Strategy

While adding more accounts and services can increase complexity, Project 3 keeps cost in mind:

- Use **lightweight, always-on** security services (GuardDuty, Security Hub) instead of heavy custom tooling.
- Targeted use of AI only on **events/findings**, not continuous data streams.
- Budgets and anomalies provide early warning before costs get out of control.
- Clear separation of accounts helps track which environment or team is spending what.

---

## Business Outcomes

With this layer in place, the RSVP platform gains:

- Stronger security posture across all environments
- Cleaner separation of dev vs prod work
- Guardrails that prevent “dangerous by accident” actions
- Clearer visibility into costs and potential anomalies
- Faster, more informed incident response via AI summaries

---

## Future Enhancements

Potential upgrades:

- Centralized logging account with S3 + CloudTrail + CloudWatch Logs aggregation
- Automated ticket creation (Jira, ServiceNow) from AI incident summaries
- Mapping incident severity to on-call schedules/pages
- More granular SCPs and permission sets as the org expands
- AI assistant for cost optimization recommendations in addition to security
