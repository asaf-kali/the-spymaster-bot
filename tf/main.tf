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

variable "sentry_dsn" {
  type      = string
  sensitive = true
}

variable "telegram_token" {
  type      = string
  sensitive = true
}

locals {
  #  Environment
  env_map = {
    "default" = "dev"
    "prod"    = "prod"
  }
  env               = local.env_map[terraform.workspace]
  # Base
  project_name      = "the-spymaster-bot"
  service_name      = "${local.project_name}-${local.env}"
  aws_account_id    = data.aws_caller_identity.current.account_id
  project_root      = "${path.module}/../"
  # Domain
  base_app_domain   = "the-spymaster.xyz"
  hosted_zone_id    = "Z0770508EK6R7V32364I"
  certificate_arn   = "arn:aws:acm:us-east-1:${local.aws_account_id}:certificate/fc0faea8-e891-438a-a779-4013ee38755f"
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