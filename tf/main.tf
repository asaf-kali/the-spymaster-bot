# Terraform

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.12.0"
    }
  }
  backend "s3" {
    bucket               = "the-spymaster-infra-tf-state"
    key                  = "bot/terraform.tfstate"
    region               = "us-east-1"
    dynamodb_table       = "the-spymaster-infra-tf-state-lock"
    workspace_key_prefix = "env"
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
  is_prod           = local.env == "prod"
  # Base
  project_name      = "the-spymaster-bot"
  service_name      = "${local.project_name}-${local.env}"
  aws_account_id    = data.aws_caller_identity.current.account_id
  # Paths
  tf_root           = abspath(path.module)
  project_root      = abspath("${path.module}/../")
  layer_src_root    = "${local.project_root}/.deployment/layer-dependencies"
  lambda_src_root   = "${local.project_root}/src/"
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
  # Encryption
  default_key_arn    = "arn:aws:kms:us-east-1:096386908883:key/0b9c713c-1c4b-43ad-84df-1f62117838f0"
  # Config
  # warmup is true if prod else false
  warmup_enabled     = local.is_prod
}

data "aws_caller_identity" "current" {}
