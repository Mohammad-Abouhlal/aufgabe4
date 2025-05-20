terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  access_key = "mock_access_key"
  secret_key = "mock_secret_key"
  region     = "eu-central-1"

  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigatewayv2   = "http://localhost:4566"
    apigateway     = "http://localhost:4566"
    beanstalk      = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    elasticache    = "http://localhost:4566"
    iam            = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    rds            = "http://localhost:4566"
    s3             = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    ses            = "http://localhost:4566"
    sns            = "http://localhost:4566"
  }

}

resource "aws_s3_bucket" "image_bucket" {
  bucket = "my-s3-bucket"

  tags = {
    Name        = "My S3 bucket"
    Environment = "Dev"
  }
}

resource "aws_dynamodb_table" "products" {
  name           = "Products"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "ProductsTable"
    Environment = "Dev"
  }
}

# 1) Topic anlegen
resource "aws_sns_topic" "my_topic" {
  name = "my-local-topic"
}

# 2) HTTP-Subscription: Nachrichten per POST an dein Backend
resource "aws_sns_topic_subscription" "http_subscription" {
  topic_arn = aws_sns_topic.my_topic.arn
  protocol  = "http"
  endpoint  = "http://backend-app:5000/notifications"
  confirmation_timeout_in_minutes = 5
}

output "sns_topic_arn" {
  value = aws_sns_topic.my_topic.arn
}