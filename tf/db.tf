# Dynamo DB

resource "aws_dynamodb_table" "persistence_table" {
  name           = "${local.service_name}-persistence-table"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "item_id"

  attribute {
    name = "item_id"
    type = "S"
  }
}
