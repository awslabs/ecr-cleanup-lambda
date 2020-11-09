resource "aws_iam_role_policy" "ecr-cleanup-lambda_role_policy" {
  name = "ecr-cleanup-lambda"
  role = aws_iam_role.ecr-cleanup-lambda_role.id

  policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Effect": "Allow",
        "Resource": "arn:aws:logs:*:*:*"
      },
      {
        "Action": [
          "ecr:BatchDeleteImage",
          "ecr:DescribeRepositories",
          "ecr:ListImages",
          "ecr:DescribeImages"
        ],
        "Effect": "Allow",
        "Resource": "*"
      },
      {
        "Action": [
          "ecs:DescribeClusters",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
          "ecs:ListClusters",
          "ecs:ListTaskDefinitions",
          "ecs:ListTasks"
        ],
        "Effect": "Allow",
        "Resource": "*"
      }
    ]
  }
  EOF
}

resource "aws_iam_role" "ecr-cleanup-lambda_role" {
  name = "ecr-cleanup-lambda"

  assume_role_policy = <<-EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
  }
  EOF
}

module "lambda_function_existing_package_local" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 1.0"

  function_name = var.NAME_OF_FUNCTION
  description   = "Lifecycle for ECR images"
  handler       = "main.handler"
  runtime       = "python3.8"

  lambda_role            = aws_iam_role.ecr-cleanup-lambda_role.arn
  create_package         = false
  create_role            = false
  local_existing_package = "../${var.NAME_OF_FUNCTION}.zip"

  environment_variables = {
    IMAGES_TO_KEEP    = tonumber(var.IMAGES_TO_KEEP),
    IGNORE_TAGS_REGEX = var.IGNORE_TAGS_REGEX,
    REGION            = var.REGION
  }

  //  allowed_triggers = {
  //    OneRule = {
  //      principal  = "events.amazonaws.com"
  //      source_arn = "arn:aws:events:eu-west-1:135367859851:rule/RunDaily"
  //    }
  //  }
}


