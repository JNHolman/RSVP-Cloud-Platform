variable "aws_region" {
  description = "AWS region for the Terraform state bootstrap resources"
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Globally unique S3 bucket name for Terraform state"
  type        = string
}

variable "lock_table_name" {
  description = "DynamoDB table used for Terraform state locking"
  type        = string
  default     = "rsvp-cloud-platform-terraform-locks"
}
