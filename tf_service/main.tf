# Terraform

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.18.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Parameters

data "aws_caller_identity" "current" {}

locals {
  project_name      = "the-spymaster-bot"
  service_name      = "${local.project_name}-${var.env}"
  aws_account_id    = data.aws_caller_identity.current.account_id
  project_root      = "${path.module}/../"
  lambda_zip_name   = "the-spymaster-bot.zip"
  layer_zip_name    = "the-spymaster-bot-layer.zip"
  base_app_domain   = "the-spymaster.xyz"
  domain_suffix_map = {
    "dev"     = "dev."
    "staging" = "staging."
    "prod"    = ""
  }
  domain_suffix      = local.domain_suffix_map[var.env]
  bot_webhook_domain = "telegram.${local.domain_suffix}${local.base_app_domain}"
  bot_kms_env_map    = {
    "dev" : "arn:aws:kms:us-east-1:${local.aws_account_id}:key/4d0d382c-dcfa-4f44-b990-c66f468dc5dd",
  }
  bot_kms_arn = local.bot_kms_env_map[var.env]
}

variable "aws_region" {
  default = "us-east-1"
}

variable "env" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Valid values for var: `dev`, `stage`, `prod`"
  }
}

# Layer

data "archive_file" "lambda_layer_code" {
  type        = "zip"
  source_dir  = "${local.project_root}/.deployment/layer-dependencies/"
  output_path = local.layer_zip_name
}

resource "aws_lambda_layer_version" "bot_dependencies_layer" {
  filename         = data.archive_file.lambda_layer_code.output_path
  layer_name       = "${local.service_name}-layer"
  source_code_hash = filebase64sha256(data.archive_file.lambda_layer_code.output_path)
  skip_destroy     = true
}

# Lambda

data "archive_file" "bot_lambda_code" {
  type        = "zip"
  source_dir  = "${local.project_root}/src"
  output_path = local.lambda_zip_name
}

resource "aws_lambda_function" "bot_handler_lambda" {
  function_name    = "${local.service_name}-lambda"
  role             = aws_iam_role.bot_lambda_exec_role.arn
  handler          = "lambda_handler.handle"
  runtime          = "python3.9"
  filename         = data.archive_file.bot_lambda_code.output_path
  source_code_hash = filebase64sha256(data.archive_file.bot_lambda_code.output_path)
  timeout          = 60
  memory_size      = 256
  publish          = true
  layers           = [
    aws_lambda_layer_version.bot_dependencies_layer.arn
  ]
  environment {
    variables = {
      ENV_FOR_DYNACONF = var.env
    }
  }
}

resource "aws_lambda_alias" "bot_handler_live_alias" {
  function_name    = aws_lambda_function.bot_handler_lambda.function_name
  function_version = aws_lambda_function.bot_handler_lambda.version
  name             = "live"
}

# API Gateway

resource "aws_apigatewayv2_api" "api_gateway" {
  name          = "${local.service_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api_gateway_integration" {
  api_id             = aws_apigatewayv2_api.api_gateway.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.bot_handler_lambda.invoke_arn
  #  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "api_gateway_route" {
  api_id    = aws_apigatewayv2_api.api_gateway.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.api_gateway_integration.id}"
}

resource "aws_lambda_permission" "bot_handler_api_gateway_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"
  function_name = aws_lambda_function.bot_handler_lambda.arn
  #  qualifier     = aws_lambda_alias.bot_handler_live_alias.name
  source_arn    = "${aws_apigatewayv2_api.api_gateway.execution_arn}/*/*/{proxy+}"
}

resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api_gateway.id
  name        = local.service_name
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw_log_group.arn

    format = jsonencode({
      request_id                = "$context.requestId"
      source_ip                 = "$context.identity.sourceIp"
      request_time              = "$context.requestTime"
      protocol                  = "$context.protocol"
      http_method               = "$context.httpMethod"
      resource_path             = "$context.resourcePath"
      route_key                 = "$context.routeKey"
      status                    = "$context.status"
      response_length           = "$context.responseLength"
      integration_error_message = "$context.integrationErrorMessage"
    }
    )
  }
}

resource "aws_cloudwatch_log_group" "api_gw_log_group" {
  name              = "/aws/api-gw/${aws_apigatewayv2_api.api_gateway.name}"
  retention_in_days = 30
}


# Lambda role

data "aws_iam_policy_document" "lambda_assume_policy_doc" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "bot_lambda_exec_role" {
  name               = "${local.service_name}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_policy_doc.json
  inline_policy {
    name   = "${local.service_name}-lambda-exec-role-policy"
    policy = jsonencode(
      {
        "Version" : "2012-10-17",
        "Statement" : [
          {
            "Effect" : "Allow",
            "Action" : [
              "logs:CreateLogGroup",
              "logs:CreateLogStream",
              "logs:PutLogEvents"
            ],
            "Resource" : "arn:aws:logs:*:*:*"
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "ssm:GetParameter",
              "ssm:GetParameters",
            ],
            "Resource" : "arn:aws:ssm:${var.aws_region}:${local.aws_account_id}:parameter/${local.service_name}-*"
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "kms:Decrypt",
            ],
            "Resource" : local.bot_kms_arn
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "dynamodb:DescribeTable",
              "dynamodb:GetItem",
              "dynamodb:PutItem",
            ],
            "Resource" : aws_dynamodb_table.persistence_table.arn
          }
        ]
      }
    )
  }
}

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

# Outputs

output "api_endpoint" {
  value = "${aws_apigatewayv2_api.api_gateway.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/"
}
