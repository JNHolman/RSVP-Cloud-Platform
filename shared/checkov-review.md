# Infrastructure security review

The reviewed [CI run](https://github.com/JNHolman/RSVP-Cloud-Platform/actions/runs/42570392336) reported 887 passes, 42 failures and 15 skips. Counts below refer to failed check/resource pairs. Several checks cover the six-account design, which was tested offline. No new suppressions were added.

| Disposition | Findings | Engineering assessment |
|---|---:|---|
| Corrected | 2 | CKV_AWS_23 on both sides of the peered MySQL connection. The Terraform rules now describe the permitted traffic. Port, direction and peer group were already constrained. |
| Accepted | 2 | CKV_AWS_260 on the public load balancers. Port 80 redirects to HTTPS. |
| Accepted | 12 | CKV2_AWS_62 and CKV_AWS_144 on six S3 buckets each. The design has no consumer for per-object notifications on these buckets. Remote replication of state, audit and operational logs would add another regional copy and custody obligations. Regional disaster recovery for these objects remains a limitation. |
| Accepted | 9 | In the governance design the audit trail archives to S3 without per-delivery SNS (252). IAM Identity Center deliberately grants the assigned administrator group a two-hour AdministratorAccess session (274). The dashboard leaves sensitive responses uncached (120, 225). Lambda integration has no HTTPS backend requiring a stage client certificate (CKV2_AWS_51). The two GET methods and their two CORS OPTIONS methods take no request body (CKV2_AWS_53, four findings). |
| Static-analysis limitation | 4 | The private EC2 port-80 rule names the load balancer group as its source (260). Three IAM checks (109, 111, 356) treated the archive KMS key policy like an identity policy. Its wildcard resource means the attached key. Administration is delegated to the owning account, and service use is constrained by the trail and encryption context. |
| Static-analysis limitation | 6 | MySQL requires secure transport in its attached parameter group (CKV2_AWS_69). Both default internet routes point to NAT; the separate peer routes target the foundation CIDR and security groups restrict database traffic (CKV2_AWS_44, twice). All three WAF configurations attach the AWS Known Bad Inputs managed group (CKV2_AWS_76 twice and 77 once). This establishes configured coverage only. |
| Unresolved | 7 | Four Lambda functions lack enforced artifact signing (272). Two VPC roots select the first two available AZ names, so placement can change if AWS changes the returned set (394). The designed organization trail has encrypted S3 delivery and file validation but no CloudWatch Logs integration (CKV2_AWS_10), limiting near-real-time monitoring through that path. |

Totals: **2 corrected, 23 accepted, 10 static-analysis limitations, 7 unresolved**. The image scan is separate; two HIGH glibc findings remained on the rebuilt candidate. [Image scan evidence](../project-2-ecs-cicd/evidence/2026-11-08.md#post-demo-image-remediation)
