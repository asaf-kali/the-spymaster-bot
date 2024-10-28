resource "aws_s3_bucket" "deployment_bucket" {
  bucket = "${local.service_name}-deployment"
}

resource "null_resource" "pip_lock" {
  provisioner "local-exec" {
    command = "cd ${local.project_root}; make lock-export"
  }
}

module "dependencies_layer" {
  source            = "./layer"
  layer_name        = "${local.service_name}-deps-layer"
  lock_file         = "${local.project_root}/poetry.lock"
  requirements_file = "${local.project_root}/requirements.lock"
  s3_bucket         = aws_s3_bucket.deployment_bucket.bucket
  skip_destroy      = true
  depends_on = [
    null_resource.pip_lock
  ]
}
