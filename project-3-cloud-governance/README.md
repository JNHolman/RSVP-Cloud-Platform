# Project 3 – AWS Multi-Account Cloud Governance & AI Incident Assistant

**Live Dashboard:**  
http://rsvp-cloud-governance-dashboard.s3-website-us-east-1.amazonaws.com/

This project simulates an enterprise AWS landing zone with:

- AWS Organizations (management, security, logging, workload accounts)
- Centralized CloudTrail & AWS Config logging
- GuardDuty & Security Hub for threat detection
- AI-powered incident summaries (Lambda + OpenAI)
- AI-powered weekly cost optimization reports
- Static React-style dashboard (no build tools) hosted on S3

Frontend is a static `index.html` React app under `dashboard/` that visualizes:

- Recent AI-analyzed GuardDuty incidents (with severity badges & modals)
- Cost optimization summaries
- Incident timeline in a CloudTrail-style view
