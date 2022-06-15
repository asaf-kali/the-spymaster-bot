terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.18.0"
    }
  }
}

provider "aws" {
  region = local.aws_region
}

# Parameters

data "aws_caller_identity" "current" {}

locals {
  project_base_name = "the-spymaster-bot"
  project_name      = "${local.project_base_name}-${var.env}"
  aws_region        = "us-east-1"
  lambda_zip_name   = "the-spymaster-bot.zip"
  account_id        = data.aws_caller_identity.current.account_id
}

variable "telegram_token" {
  type      = string
  sensitive = true
}

variable "env" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Valid values for var: `dev`, `stage`, `prod`"
  }
}

# Secrets

resource "aws_kms_key" "bot_kms_key" {
  description = "KMS key for bot service on ${var.env} environment"
}

resource "aws_kms_alias" "bot_kms_key_alias" {
  name          = "alias/${local.project_name}-key"
  target_key_id = aws_kms_key.bot_kms_key.id
}

resource "aws_ssm_parameter" "bot_token" {
  name   = "${local.project_name}-token"
  type   = "SecureString"
  value  = var.telegram_token
  key_id = aws_kms_key.bot_kms_key.arn
}

# Lambda handler

data "archive_file" "bot_lambda_code" {
  type        = "zip"
  source_dir  = "${path.module}/bot/"
  output_path = local.lambda_zip_name
}

resource "aws_lambda_function" "bot_handler_lambda" {
  function_name = "${local.project_name}-lambda"
  role          = aws_iam_role.bot_lambda_exec_role.arn
  handler       = "lambda_handler.handle"
  runtime       = "python3.9"
  filename      = data.archive_file.bot_lambda_code.output_path
  environment {
    variables = {
      API_PREFIX = aws_apigatewayv2_api.api.api_endpoint
      PATH_KEY   = random_id.random_path.hex
    }
  }
}

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
  name               = "${local.project_name}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_policy_doc.json
  inline_policy {
    name   = "${local.project_name}-lambda-exec-role-policy"
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
              "ssm:GetParameterHistory",
              "ssm:GetParameters",
              "ssm:GetParametersByPath",
            ],
            "Resource" : aws_ssm_parameter.bot_token.arn
          },
          # {
          #   "Effect" : "Allow",
          #   "Action" : [
          #     "kms:Decrypt",
          #   ],
          #   "Resource" : aws_kms_key.bot_kms_key.arn
          # },
        ]
      }
    )
  }
}

resource "aws_lambda_permission" "apigw" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bot_handler_lambda.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# API Gateway

resource "random_id" "random_path" {
  byte_length = 32
}

resource "aws_apigatewayv2_api" "api" {
  name          = "${local.project_base_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.bot_handler_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "api_route" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "ANY /${random_id.random_path.hex}/{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

# Check if this is actually needed
resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "${local.project_name}-api"
  auto_deploy = true
}

# Outputs

output "api_endpoint" {
  value = aws_apigatewayv2_api.api.api_endpoint
}

output "random_path" {
  value = random_id.random_path.hex
}

output "trigger_endpoint" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/${random_id.random_path.hex}/"
}
