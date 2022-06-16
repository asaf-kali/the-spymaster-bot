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

resource "random_id" "random_path" {
  byte_length = 32
}

resource "aws_kms_key" "bot_kms_key" {
  description = "KMS key for bot service on ${var.env} environment"
}

resource "aws_kms_alias" "bot_kms_key_alias" {
  name          = "alias/${local.project_name}-key"
  target_key_id = aws_kms_key.bot_kms_key.id
}

resource "aws_ssm_parameter" "telegram_token" {
  name   = "${local.project_name}-telegram-token"
  type   = "SecureString"
  value  = var.telegram_token
  key_id = aws_kms_key.bot_kms_key.arn
}

resource "aws_ssm_parameter" "lambda_auth_token" {
  name   = "${local.project_name}-auth-token"
  type   = "SecureString"
  value  = random_id.random_path.hex
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
}

resource "aws_lambda_function_url" "bot_handler_lambda_url" {
  function_name      = aws_lambda_function.bot_handler_lambda.function_name
  authorization_type = "NONE"
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
            ],
            "Resource" : aws_ssm_parameter.telegram_token.arn
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "ssm:GetParameter",
            ],
            "Resource" : aws_ssm_parameter.lambda_auth_token.arn
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

# Outputs

output "bot_trigger_url" {
  value = aws_lambda_function_url.bot_handler_lambda_url.function_url
}
