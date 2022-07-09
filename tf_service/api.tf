# API Gateway

resource "aws_apigatewayv2_api" "api_gateway" {
  name          = "${local.service_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api_gateway_integration" {
  api_id             = aws_apigatewayv2_api.api_gateway.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.service_lambda.invoke_arn
}

resource "aws_apigatewayv2_route" "api_gateway_route" {
  api_id    = aws_apigatewayv2_api.api_gateway.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.api_gateway_integration.id}"
}

resource "aws_lambda_permission" "bot_handler_api_gateway_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"
  function_name = aws_lambda_function.service_lambda.arn
  source_arn    = "${aws_apigatewayv2_api.api_gateway.execution_arn}/*/*/{proxy+}"
}

resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api_gateway.id
  name        = local.service_name
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gw_log_group.arn

    format = jsonencode({
      request_id                = "$context.requestId"
      source_ip                 = "$context.identity.sourceIp"
      request_time              = "$context.requestTime"
      protocol                  = "$context.protocol"
      http_method               = "$context.httpMethod"
      resource_path             = "$context.resourcePath"
      route_key                 = "$context.routeKey"
      status                    = "$context.status"
      response_length           = "$context.responseLength"
      integration_error_message = "$context.integrationErrorMessage"
    }
    )
  }
}

resource "aws_cloudwatch_log_group" "api_gw_log_group" {
  name              = "/aws/api-gw/${aws_apigatewayv2_api.api_gateway.name}"
  retention_in_days = 30
}

output "api_endpoint_url" {
  value = local.bot_endpoint_url
}
