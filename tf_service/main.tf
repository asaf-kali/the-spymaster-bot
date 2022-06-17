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
  aws_account       = "096386908883"
  project_name      = "${local.project_base_name}-${var.env}"
  aws_region        = "us-east-1"
  lambda_zip_name   = "the-spymaster-bot.zip"
  layer_zip_name    = "the-spymaster-bot-layer.zip"
  account_id        = data.aws_caller_identity.current.account_id
  bot_kms_arn       = var.bot_kms_env_map[var.env]
  project_root      = "${path.module}/../"
}

variable "env" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Valid values for var: `dev`, `stage`, `prod`"
  }
}

variable "bot_kms_env_map" {
  type    = map(string)
  default = {
    "dev" : "arn:aws:kms:us-east-1:096386908883:key/4d0d382c-dcfa-4f44-b990-c66f468dc5dd",
  }
}

# Lambda handler

data "archive_file" "lambda_layer_code" {
  type        = "zip"
  source_dir  = "${local.project_root}/.deployment/layer-dependencies/"
  output_path = local.layer_zip_name
}

resource "aws_lambda_layer_version" "bot_dependencies_layer" {
  filename         = data.archive_file.lambda_layer_code.output_path
  layer_name       = "${local.project_name}-layer"
  source_code_hash = filebase64sha256(data.archive_file.lambda_layer_code.output_path)
  skip_destroy     = true
}

data "archive_file" "bot_lambda_code" {
  type        = "zip"
  source_dir  = "${local.project_root}/src"
  output_path = local.lambda_zip_name
}

resource "aws_lambda_function" "bot_handler_lambda" {
  function_name    = "${local.project_name}-lambda"
  role             = aws_iam_role.bot_lambda_exec_role.arn
  handler          = "lambda_handler.handle"
  runtime          = "python3.9"
  filename         = data.archive_file.bot_lambda_code.output_path
  source_code_hash = filebase64sha256(data.archive_file.bot_lambda_code.output_path)
  layers           = [
    aws_lambda_layer_version.bot_dependencies_layer.arn
  ]
  environment {
    variables = {
      ENV_FOR_DYNACONF = var.env
    }
  }
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
              "ssm:GetParameters",
            ],
            "Resource" : "arn:aws:ssm:us-east-1:${local.aws_account}:parameter/${local.project_name}-*"
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "kms:Decrypt",
            ],
            "Resource" : local.bot_kms_arn
          },
        ]
      }
    )
  }
}

# Dynamo DB

resource "aws_dynamodb_table" "state_table" {
  name           = "${local.project_name}-state-table"
  billing_mode   = "PROVISIONED"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }
}

# Outputs

output "bot_trigger_url" {
  value = aws_lambda_function_url.bot_handler_lambda_url.function_url
}