# Variables

variable "layer_name" {
  description = "Name of the Lambda Layer"
}

variable "s3_bucket" {
  description = "S3 bucket for Lambda layer ZIP file"
}

variable "runtime" {
  default     = "python3.11"
  description = "Runtime version for Lambda layer"
}

variable "s3_key_prefix" {
  default     = "lambda_layers/"
  description = "S3 prefix for Lambda layer ZIP file"
}

variable "lock_file" {
  default     = "poetry.lock"
  description = "Path to dependencies a lock file"
}

variable "requirements_file" {
  default     = "requirements.txt"
  description = "Path to the pip requirements file"
}

variable "skip_destroy" {
  default     = true
  description = "Skip destroy for the Lambda Layer"
}

locals {
  zip_path = abspath("${path.module}/../layer-${var.layer_name}.zip")
}

# Generate Lambda Layer ZIP and upload to S3

resource "null_resource" "lambda_layer" {
  triggers = {
    requirements_file = filesha256(var.lock_file)
  }

  # provisioner "local-exec" {
  #   command = <<EOT
  #     cd app && \
  #     mkdir -p python && \
  #     poetry export -f requirements.txt | pip install -r /dev/stdin -t python/ && \
  #     zip -r ../lambda_layer.zip python
  #   EOT
  # }

  provisioner "local-exec" {
    command = <<EOT
      image_name="public.ecr.aws/sam/build-${var.runtime}"
      export_folder=$(mktemp -d)
      update_pip_cmd="pip install --upgrade pip"
      install_dependencies_cmd="pip install -r ${var.requirements_file} -t $export_folder"
      docker_cmd="$update_pip_cmd; $install_dependencies_cmd; exit"
      docker run -v "$PWD":/var/task "$image_name" /bin/sh -c "$docker_cmd"
      zip -r ${local.zip_path} $export_folder
    EOT
  }

  provisioner "local-exec" {
    command = <<EOT
      aws s3 cp ${local.zip_path} s3://${var.s3_bucket}/${var.s3_key_prefix}${var.layer_name}.zip
    EOT
  }
}

# Create Lambda Layer

resource "aws_lambda_layer_version" "layer" {
  layer_name   = var.layer_name
  s3_bucket    = var.s3_bucket
  s3_key       = "${var.s3_key_prefix}${var.layer_name}.zip"
  skip_destroy = var.skip_destroy
}

# Outputs

output "arn" {
  value = aws_lambda_layer_version.layer.arn
}

output "version" {
  value = aws_lambda_layer_version.layer.version
}
