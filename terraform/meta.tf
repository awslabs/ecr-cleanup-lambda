terraform {
  required_version = ">= 0.13.0, < 0.14.0"

  required_providers {
    aws = {
      version = "~> 3.14.1"
      source  = "hashicorp/aws"
    }
  }

/*  backend "s3" {
    bucket  = "hopin-terraform-remote-state"
    key     = "evil/eu-west-1/iam/terraform.tfstate"
    region  = "eu-west-1"
    encrypt = true
  }*/
}

provider "aws" {
  region = "eu-west-1"
}