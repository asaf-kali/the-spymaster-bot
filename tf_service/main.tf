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
    "dev" : "arn:aws:kms:us-east-1:096386908883:key/4d0d382c-dcfa-4f44-b990-c66f468dc5dd",
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

# Outputs

output "api_endpoint" {
  value = "${aws_apigatewayv2_api.api_gateway.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/"
}
