# Dynamo DB

resource "aws_dynamodb_table" "persistence_table" {
  name           = "${local.service_name}-persistence-table"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "item_id"

  attribute {
    name = "item_id"
    type = "S"
  }
}
