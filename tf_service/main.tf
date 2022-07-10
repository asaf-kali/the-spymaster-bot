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

variable "aws_region" {
  default = "us-east-1"
}

locals {
  #  Environment
  env_map = {
    "default" = "dev"
    "prod"    = "prod"
  }
  env            = local.env_map[terraform.workspace]
  # Base
  project_name   = "the-spymaster-bot"
  service_name   = "${local.project_name}-${local.env}"
  aws_account_id = data.aws_caller_identity.current.account_id
  project_root   = "${path.module}/../"
  # Secrets
  kms_env_map    = {
    "dev" : "arn:aws:kms:us-east-1:096386908883:key/4d0d382c-dcfa-4f44-b990-c66f468dc5dd",
    "prod" : "arn:aws:kms:us-east-1:096386908883:key/0b9c713c-1c4b-43ad-84df-1f62117838f0",
  }
  kms_arn           = local.kms_env_map[local.env]
  # Domain
  base_app_domain   = "the-spymaster.xyz"
  hosted_zone_id    = "Z0770508EK6R7V32364I"
  certificate_arn   = "arn:aws:acm:us-east-1:096386908883:certificate/fc0faea8-e891-438a-a779-4013ee38755f"
  domain_suffix_map = {
    "dev"     = "dev."
    "staging" = ""
    "prod"    = ""
  }
  domain_suffix      = local.domain_suffix_map[local.env]
  bot_webhook_domain = "telegram.${local.domain_suffix}${local.base_app_domain}"
  bot_endpoint_url   = "${aws_apigatewayv2_api.api_gateway.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/"
}

data "aws_caller_identity" "current" {}
