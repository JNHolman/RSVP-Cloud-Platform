variable "foundation_db" {
  description = "Private database and networking details from the portfolio foundation. Omit for an independent fixture deployment."
  type = object({
    vpc_id                  = string
    vpc_cidr                = string
    private_route_table_ids = set(string)
    security_group_id       = string
    resource_id             = string
    hostname                = string
    database                = string
  })
  default = null
}

locals {
  database_environment = var.foundation_db == null ? [] : [
    { name = "DB_MODE", value = "rds" },
    { name = "DB_HOST", value = var.foundation_db.hostname },
    { name = "DB_NAME", value = var.foundation_db.database },
    { name = "RDS_CA_FILE", value = "/app/rds-ca.pem" }
  ]
}

resource "aws_vpc_peering_connection" "foundation" {
  count       = var.foundation_db == null ? 0 : 1
  vpc_id      = aws_vpc.this.id
  peer_vpc_id = var.foundation_db.vpc_id
  auto_accept = true
  tags        = { Name = "${local.name_prefix}-foundation" }
}

resource "aws_route" "foundation_return" {
  for_each                  = var.foundation_db == null ? toset([]) : var.foundation_db.private_route_table_ids
  route_table_id            = each.key
  destination_cidr_block    = aws_vpc.this.cidr_block
  vpc_peering_connection_id = aws_vpc_peering_connection.foundation[0].id
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_database" {
  count                        = var.foundation_db == null ? 0 : 1
  security_group_id            = aws_security_group.ecs_service.id
  referenced_security_group_id = var.foundation_db.security_group_id
  from_port                    = 3306
  to_port                      = 3306
  ip_protocol                  = "tcp"
  depends_on                   = [aws_vpc_peering_connection.foundation]
}

resource "aws_vpc_security_group_ingress_rule" "database_from_ecs" {
  count                        = var.foundation_db == null ? 0 : 1
  security_group_id            = var.foundation_db.security_group_id
  referenced_security_group_id = aws_security_group.ecs_service.id
  from_port                    = 3306
  to_port                      = 3306
  ip_protocol                  = "tcp"
  depends_on                   = [aws_vpc_peering_connection.foundation]
}

resource "aws_iam_role_policy" "read_foundation_db" {
  count = var.foundation_db == null ? 0 : 1
  name  = "${local.name_prefix}-read-foundation-db"
  role  = aws_iam_role.ecs_task_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "rds-db:connect"
      Resource = "arn:aws:rds-db:${var.aws_region}:${data.aws_caller_identity.current.account_id}:dbuser:${var.foundation_db.resource_id}/rsvp_reader"
    }]
  })
}
