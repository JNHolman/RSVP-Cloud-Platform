locals {
  tags = {
    Project     = var.project_name
    Environment = "lab"
    Owner       = "Josh Holman"
  }
}

# ─────────────────────────────────────────────
# ORG LAYER (MODELED)
# ─────────────────────────────────────────────
module "org" {
  source = "./org"

  aws_region     = var.aws_region
  project_name   = var.project_name
  account_labels = var.account_labels
  tags           = local.tags

  providers = {
    aws = aws
  }
}

# ─────────────────────────────────────────────
# LOGGING LAYER
# ─────────────────────────────────────────────
module "logging" {
  source = "./logging"

  aws_region   = var.aws_region
  project_name = var.project_name
  tags         = local.tags

  # In a real org you’d point this to the logging account provider
  providers = {
    aws = aws.logging
  }
}

# ─────────────────────────────────────────────
# SECURITY LAYER
# GuardDuty, SecurityHub, Config, AI Incident Lambda, AI Cost Lambda
# ─────────────────────────────────────────────
module "security" {
  source = "./security"

  aws_region     = var.aws_region
  project_name   = var.project_name
  alert_email    = var.alert_email
  openai_api_key = var.openai_api_key
  tags           = local.tags

  providers = {
    aws = aws.security
  }

  # We’ll feed in logging outputs once logging module is built
  logging_bucket_arn = module.logging.cloudtrail_bucket_arn
}

# ─────────────────────────────────────────────
# WORKLOAD LAYER
# EventBridge rules, cross-account roles, alarms targeting security
# ─────────────────────────────────────────────
module "workload" {
  source = "./workload"

  aws_region   = var.aws_region
  project_name = var.project_name
  tags         = local.tags

  providers = {
    aws = aws.workload
  }

  security_alert_topic_arn     = module.security.security_alert_topic_arn
  ai_incidents_table_name      = module.security.ai_incidents_table_name
  ai_cost_summaries_table_name = module.security.ai_cost_summaries_table_name
}

output "dashboard_api_url" {
  value = module.workload.dashboard_api_url
}
