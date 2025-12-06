resource "aws_dynamodb_table" "ai_incidents" {
  name         = "${var.project_name}-ai-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "finding_id"

  attribute {
    name = "finding_id"
    type = "S"
  }

  tags = merge(
    var.tags,
    {
      "Component" = "security"
      "Service"   = "AI-Incidents"
    }
  )
}
