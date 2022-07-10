# Layer

data "archive_file" "layer_code_archive" {
  type        = "zip"
  source_dir  = "${local.project_root}/.deployment/layer-dependencies/"
  output_path = "layer.zip"
}

resource "aws_lambda_layer_version" "dependencies_layer" {
  filename         = data.archive_file.layer_code_archive.output_path
  layer_name       = "${local.service_name}-layer"
  source_code_hash = filebase64sha256(data.archive_file.layer_code_archive.output_path)
  skip_destroy     = true
}

# Lambda

data "archive_file" "service_code_archive" {
  type        = "zip"
  source_dir  = "${local.project_root}/src"
  output_path = "service.zip"
}

resource "aws_lambda_function" "service_lambda" {
  function_name                  = "${local.service_name}-lambda"
  role                           = aws_iam_role.lambda_exec_role.arn
  handler                        = "lambda_handler.handle"
  runtime                        = "python3.9"
  filename                       = data.archive_file.service_code_archive.output_path
  source_code_hash               = filebase64sha256(data.archive_file.service_code_archive.output_path)
  timeout                        = 30
  memory_size                    = 200
  reserved_concurrent_executions = 5
  layers                         = [
    aws_lambda_layer_version.dependencies_layer.arn
  ]
  environment {
    variables = {
      ENV_FOR_DYNACONF = local.env
    }
  }
}

# Lambda role

data "aws_iam_policy_document" "lambda_assume_policy_doc" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name               = "${local.service_name}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_policy_doc.json
  inline_policy {
    name   = "${local.service_name}-lambda-exec-role-policy"
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
            "Resource" : "arn:aws:ssm:${var.aws_region}:${local.aws_account_id}:parameter/${local.service_name}-*"
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "kms:Decrypt",
            ],
            "Resource" : local.kms_arn
          },
          {
            "Effect" : "Allow",
            "Action" : [
              "dynamodb:DescribeTable",
              "dynamodb:GetItem",
              "dynamodb:PutItem",
            ],
            "Resource" : aws_dynamodb_table.persistence_table.arn
          }
        ]
      }
    )
  }
}
