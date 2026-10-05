# Authenticated Governance Dashboard API

This stack replaces the earlier public HTTP API with a Regional API Gateway REST API so the edge can be protected by AWS WAF.

Controls implemented:

- Amazon Cognito user-pool authorization on all data routes
- one explicit HTTPS-only CORS origin; wildcard origins are rejected by Terraform validation
- AWS WAF managed common, known-bad-input, and IP-reputation rules
- per-IP WAF rate limiting
- API Gateway steady-state and burst throttling
- CloudWatch access logs and metrics without full request/response data tracing
- X-Ray tracing
- bounded Lambda concurrency and DynamoDB result size
- least-privilege DynamoDB table ARNs bound to the current AWS account
- security response headers and no-store caching

The `OPTIONS` routes remain unauthenticated for browser preflight; the actual `GET` routes require Cognito authentication.
