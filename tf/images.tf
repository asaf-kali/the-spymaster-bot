# Vars and data

locals {
  lock_file      = "${local.project_root}/poetry.lock"
  lock_file_sha = filebase64sha256(local.lock_file)
  app_dockerfile = "${local.project_root}/Dockerfile"
}

# ECR Repo

resource "aws_ecr_repository" "ecr_repo" {
  name = "${local.service_name}-ecr"
}

resource "aws_ecr_lifecycle_policy" "ecr_lifecycle_policy" {
  repository = aws_ecr_repository.ecr_repo.name
  policy     = <<EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 3 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 3
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF
}

# Prepare

resource "null_resource" "lock_export" {
  triggers = {
    lock_file = local.lock_file_sha
  }

  provisioner "local-exec" {
    command = <<EOF
           cd ${local.project_root}; make lock-export || exit 1
       EOF
  }
}

module "app_archive" {
  source     = "github.com/asaf-kali/resources//tf/filtered_archive"
  name       = "service"
  source_dir = local.lambda_src_root
  exclude_patterns = [
    ".coverage",
    "**/__pycache__/**",
    "**/.pytest_cache/**",
  ]
}

# Image

module "app_image" {
  name           = "app"
  source         = "github.com/asaf-kali/resources//tf/ecr_builder"
  aws_account_id = local.aws_account_id
  aws_region     = var.aws_region
  build_dir      = local.project_root
  docker_file    = local.app_dockerfile
  ecr_name       = aws_ecr_repository.ecr_repo.name
  ecr_url        = aws_ecr_repository.ecr_repo.repository_url
  src_image      = "public.ecr.aws/lambda/python"
  src_tag        = local.python_version
  triggers = {
    docker_file = filebase64sha256(local.app_dockerfile)
    lock_file  = local.lock_file_sha
    source_dir = module.app_archive.output_sha
  }
  depends_on = [
    null_resource.lock_export
  ]
}
