# Project 3 — Multi-Account Security, Governance & AI Incident Response

**Deployed:** February 3, 2026  
**Region:** us-east-1  
**Dashboard URL:** http://rsvp-cloud-governance-dashboard.s3-website-us-east-1.amazonaws.com/  
**API URL:** https://yzrmqj3ti7.execute-api.us-east-1.amazonaws.com

---

## 🚀 Overview

Project 3 demonstrates enterprise-grade cloud governance with centralized security monitoring, compliance automation, and AI-powered incident analysis. This is the "governance layer" that sits above workload accounts to provide security, cost optimization, and compliance guardrails.

**Key Achievement:** Full end-to-end AI-powered security operations - from GuardDuty finding detection → AI analysis → actionable incident reports → dashboard visualization.

---

## ✅ What's Working

### Security Automation
- ✅ **GuardDuty** detecting real security findings
- ✅ **EventBridge** routing findings to Lambda
- ✅ **AI Incident Lambda** analyzing findings with OpenAI GPT-4
- ✅ **DynamoDB** storing structured incident data
- ✅ **SNS** for alert escalation
- ✅ **Dashboard** displaying real-time AI analysis

### Cost Optimization
- ✅ **AI Cost Lambda** analyzing AWS spending patterns
- ✅ **OpenAI integration** generating actionable recommendations
- ✅ **Cost Explorer** data integration
- ✅ **Weekly automated reports**

### Compliance & Monitoring
- ✅ **Security Hub** centralized security posture
- ✅ **AWS Config** compliance rules and monitoring
- ✅ **CloudTrail** centralized logging
- ✅ **Multi-account organization** structure

---

## 📊 Live Metrics

**Current Status (as of Feb 3, 2026):**
- **3 GuardDuty findings** analyzed by AI
- **3 Cost optimization reports** generated
- **100% incident processing** success rate
- **Real-time dashboard** operational

**AI-Analyzed Incidents:**
1. **SSH Brute Force** (Severity 8) - EC2 instance under attack
2. **S3 Public Access** (Severity 5) - Bucket policy misconfiguration
3. **IAM Privilege Escalation** (Severity 7) - Suspicious policy attachment

**Cost Optimization Reports:**
1. NAT Gateway consolidation ($95-120/month savings)
2. RDS automated scheduling ($82/month savings)
3. ECR lifecycle policies ($15-20/month savings)

---

## 🏗️ Architecture

### Multi-Account Structure
```
Management Account (us-east-1)
├── Security Account
│   ├── GuardDuty (detector: 1485729971444a2a9388f537bd26ae8a)
│   ├── Security Hub (enabled)
│   ├── AWS Config (recorder active)
│   ├── AI Incident Lambda (rsvp-cloud-governance-ai-incident-reporter)
│   └── AI Cost Lambda (rsvp-cloud-governance-ai-cost-analyzer)
├── Logging Account
│   ├── Central CloudTrail
│   ├── Config logs
│   └── S3 archival
└── Workload Account
    ├── Projects 1 & 2 (ECS, EC2, RDS, ALB)
    └── EventBridge automation
```

### AI Incident Response Flow
```
GuardDuty Finding
    ↓
EventBridge Rule
    ↓
AI Incident Lambda
    ├→ OpenAI GPT-4 (analysis)
    ├→ DynamoDB (storage)
    └→ SNS (alerting)
    ↓
API Gateway
    ↓
Dashboard (real-time display)
```

### Cost Analysis Flow
```
EventBridge Schedule (weekly)
    ↓
AI Cost Lambda
    ├→ Cost Explorer (data retrieval)
    ├→ OpenAI GPT-4 (analysis)
    └→ DynamoDB (storage)
    ↓
API Gateway
    ↓
Dashboard (insights display)
```

---

## 🔧 Infrastructure Components

### Security Services
- **GuardDuty**: Threat detection across EC2, S3, IAM
- **Security Hub**: Centralized security findings aggregation
- **AWS Config**: Compliance rules (root MFA, IAM key rotation, S3 public access)
- **CloudTrail**: API activity logging and auditing

### AI/Automation
- **Lambda Functions**:
  - `ai-incident-reporter`: Analyzes GuardDuty findings with GPT-4
  - `ai-cost-analyzer`: Generates cost optimization recommendations
  - `dashboard-api`: Serves data to frontend
- **EventBridge**: Automated triggers for incident analysis and cost reports
- **DynamoDB Tables**:
  - `ai-incidents`: Stores analyzed security findings
  - `ai-cost-summaries`: Stores optimization reports

### API & Frontend
- **API Gateway**: RESTful endpoints (`/incidents`, `/cost-summary`)
- **S3 Static Website**: React-based dashboard
- **Real-time data**: No caching, always current

---

## 📸 Evidence Screenshots

### Dashboard & UI
1. **dashboard-overview.png** - Main governance platform interface
2. **dashboard-insights.png** - Security and cost insights
3. **incident-detail-modal.png** - Detailed AI incident analysis

### AWS Security Services
4. **guardduty-summary.png** - GuardDuty findings overview
5. **security-hub-summary.png** - Security Hub posture
6. **aws-config-dashboard.png** - Config compliance rules

### Governance & IAM
7. **organizations-accounts.png** - Multi-account structure
8. **iam-roles-overview.png** - Governance IAM roles
9. **iam-role-config-detail.png** - Config service role
10. **iam-role-config-trust.png** - Trust relationships
11. **cloudtrail-event-history.png** - API activity logs

---

## 🎯 What This Demonstrates

### Enterprise Cloud Governance
- Multi-account organization design
- Centralized security monitoring
- Compliance automation
- Cost governance

### AI/ML Integration
- Real-world OpenAI API usage
- Intelligent incident triage
- Automated cost optimization recommendations
- Natural language insights from raw security data

### Modern DevOps Practices
- Infrastructure as Code (Terraform)
- Event-driven architecture (EventBridge)
- Serverless computing (Lambda)
- API-first design (API Gateway)

### Production Readiness
- Error handling and graceful degradation
- Structured logging
- Immutable deployments
- Audit trails

---

## 💰 Cost Breakdown

**Estimated Monthly Cost:** ~$25-35

- **GuardDuty**: ~$10/month (threat detection)
- **Security Hub**: ~$5/month (findings ingestion)
- **Config**: ~$3/month (rules + recorder)
- **Lambda**: ~$2/month (AI analysis + API)
- **DynamoDB**: ~$1/month (on-demand)
- **CloudTrail**: ~$2/month (logging)
- **S3**: <$1/month (dashboard + logs)
- **API Gateway**: <$1/month (low traffic)

**OpenAI API:** ~$0.50/month (GPT-4o-mini for analysis)

---

## 🔑 Key Technical Decisions

### Why ECS over Kubernetes for Projects 1 & 2?
Simpler operations, native AWS integration, sufficient for scale demonstrated.

### Why GPT-4o-mini instead of GPT-4?
Cost-effective for structured analysis tasks, sufficient reasoning capability for incident triage and cost optimization.

### Why DynamoDB over RDS?
Serverless, pay-per-use, perfect for intermittent workload (incident storage), no maintenance overhead.

### Why EventBridge over direct Lambda triggers?
Decoupled architecture, easier to add new consumers, built-in retry logic, better observability.

### Why HTTP instead of HTTPS for dashboard?
Cost optimization for demo - HTTPS requires domain ($12/year) + ACM certificate management. In production, would add HTTPS listener at ALB.

---

## 🚀 Future Enhancements

**Security:**
- [ ] Cross-region GuardDuty aggregation
- [ ] Automated remediation workflows (Lambda → SSM)
- [ ] Service Control Policies (SCPs) for preventive controls
- [ ] IAM Access Analyzer integration

**Cost:**
- [ ] Reserved Instance recommendations
- [ ] Savings Plans automation
- [ ] Budget alerts with predictive analytics
- [ ] Rightsizing recommendations

**AI/Automation:**
- [ ] Slack/Teams integration for incident notifications
- [ ] AI-powered remediation suggestions
- [ ] Trend analysis across incidents
- [ ] Custom ML models for anomaly detection

**Compliance:**
- [ ] CIS AWS Foundations Benchmark automation
- [ ] PCI-DSS compliance pack
- [ ] Automated compliance reporting
- [ ] Drift detection and alerts

---

## 📚 Interview Talking Points

**Question: "How does the AI incident analysis work?"**

*"When GuardDuty detects a security finding, EventBridge routes it to a Lambda function that sends the raw finding data to OpenAI's GPT-4o-mini API. The AI analyzes the finding and returns structured JSON with: a human-readable summary, root cause analysis, impacted resources, recommended remediation steps, escalation priority, and business impact assessment. This gets stored in DynamoDB and displayed on the dashboard in real-time. The whole flow takes about 2-3 seconds."*

**Question: "Why use AI for this instead of predefined playbooks?"**

*"AI provides context-aware analysis that adapts to new threat types without manual playbook updates. It can synthesize information from multiple fields in the finding and generate specific, actionable recommendations rather than generic templates. For example, it might suggest specific security group changes based on the exact IP addresses in the finding. It also explains the business impact in natural language, which helps with executive communication."*

**Question: "How would you handle API key security in production?"**

*"In production, I'd use AWS Secrets Manager for the OpenAI API key with automatic rotation. The Lambda would retrieve the key at runtime using IAM role credentials. I'd also implement request throttling to prevent unexpected API costs, add CloudWatch alarms for abnormal usage patterns, and use VPC endpoints to ensure the Lambda communicates securely with AWS services."*

---

## 📁 Project Structure
```
project-3-cloud-governance/
├── evidence/
│   ├── README.md (this file)
│   ├── deployment/
│   │   ├── outputs.json
│   │   └── deployed_at.txt
│   └── screenshots/ (15 images)
├── org/ (AWS Organizations modeling)
├── logging/ (CloudTrail, Config logs)
├── security/ (GuardDuty, Lambdas, DynamoDB)
├── workload/ (EventBridge, API Gateway, Dashboard)
├── dashboard/ (Static website HTML)
└── main.tf (Root module)
```

---

**Author:** Josh Holman  
**Portfolio:** https://github.com/djinfamousone/RSVP-Cloud-Platform  
**Date:** February 3, 2026  
**Status:** ✅ Production-ready demo
