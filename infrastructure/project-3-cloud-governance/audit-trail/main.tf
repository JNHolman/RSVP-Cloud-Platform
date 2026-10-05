resource "aws_cloudtrail" "organization" {
  name                          = var.trail_name
  s3_bucket_name                = var.log_archive_bucket_name
  kms_key_id                    = var.log_archive_kms_key_arn
  include_global_service_events = true
  is_multi_region_trail         = true
  is_organization_trail         = true
  enable_log_file_validation    = true
  enable_logging                = true

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }
}
