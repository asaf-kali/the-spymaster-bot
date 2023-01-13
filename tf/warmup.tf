# Lambda warmup event

resource "aws_cloudwatch_event_rule" "lambda_warmup_rule" {
  name                = "${local.service_name}-warmup"
  schedule_expression = "rate(3 minutes)"
}

resource "aws_cloudwatch_event_target" "lambda_warmup_target" {
  rule  = aws_cloudwatch_event_rule.lambda_warmup_rule.name
  arn   = aws_lambda_function.service_lambda.arn
  input = <<EOF
{
  "body": "{ \"action\": \"warmup\" }"
}
EOF
}

resource "aws_lambda_permission" "lambda_warmup_permission" {
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_warmup_rule.arn
  function_name = aws_lambda_function.service_lambda.function_name
}
