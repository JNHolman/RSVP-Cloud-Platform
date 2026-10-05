output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "lock_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}

output "state_kms_key_arn" {
  value = aws_kms_key.terraform_state.arn
}
