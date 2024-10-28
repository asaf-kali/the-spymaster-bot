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

variable "temp_zip_path" {
  default     = "lambda_layer.zip"
  description = "Path to the temporary Lambda Layer ZIP file"
}

# Generate Lambda Layer ZIP and upload to S3

resource "null_resource" "build_layer" {
  triggers = {
    lock_file = filesha256(var.lock_file)
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
      cp ${var.requirements_file} $export_folder/requirements.txt
      cd $export_folder
      update_pip_cmd="pip install --upgrade pip"
      install_dependencies_cmd="pip install -r requirements.txt -t ."
      docker_cmd="$update_pip_cmd; $install_dependencies_cmd; exit"
      docker run -v "$PWD":/var/task "$image_name" /bin/sh -c "$docker_cmd"
      zip -r ${var.temp_zip_path} $export_folder
    EOT
  }

  provisioner "local-exec" {
    command = <<EOT
      aws s3 cp ${var.temp_zip_path} s3://${var.s3_bucket}/${var.s3_key_prefix}${var.layer_name}.zip
    EOT
  }
}

# Create Lambda Layer

resource "aws_lambda_layer_version" "layer_version" {
  layer_name   = var.layer_name
  s3_bucket    = var.s3_bucket
  s3_key       = "${var.s3_key_prefix}${var.layer_name}.zip"
  skip_destroy = var.skip_destroy
  source_code_hash = filebase64sha256(var.lock_file)
  depends_on = [
    null_resource.build_layer
  ]
}

# Outputs

output "arn" {
  value = aws_lambda_layer_version.layer_version.arn
}

output "version" {
  value = aws_lambda_layer_version.layer_version.version
}
