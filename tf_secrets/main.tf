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

locals {
  project_name = "the-spymaster-bot"
  service_name = "${local.project_name}-${var.env}"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "env" {
  type    = string
  default = "dev"

  validation {
    condition     = contains(["dev", "stage", "prod"], var.env)
    error_message = "Valid values for env: `dev`, `stage`, `prod`"
  }
}

variable "sentry_dsn" {
  type      = string
  sensitive = true
}

variable "telegram_token" {
  type      = string
  sensitive = true
}

# Resources

resource "aws_kms_key" "bot_kms_key" {
  description = "KMS key for bot service on ${var.env} environment"
}

resource "aws_kms_alias" "bot_kms_key_alias" {
  name          = "alias/${local.service_name}-key"
  target_key_id = aws_kms_key.bot_kms_key.id
}

resource "aws_ssm_parameter" "sentry_dsn" {
  name   = "${local.service_name}-sentry-dsn"
  type   = "SecureString"
  value  = var.sentry_dsn
  key_id = aws_kms_key.bot_kms_key.arn
}

resource "aws_ssm_parameter" "telegram_token" {
  name   = "${local.service_name}-telegram-token"
  type   = "SecureString"
  value  = var.telegram_token
  key_id = aws_kms_key.bot_kms_key.arn
}

# Output

output "bot_kms_key_arn" {
  value = aws_kms_key.bot_kms_key.arn
}
