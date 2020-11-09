variable "DRYRUN" {
  default = false
}

variable "IMAGES_TO_KEEP" {
  type = string
  default = 1
}

variable "IGNORE_TAGS_REGEX" {
  default = "whatever"
}

variable "NAME_OF_FUNCTION" {
  default = "ecr-cleanup-lambda"
}

variable "REGION" {
  default = "eu-west-1"
}