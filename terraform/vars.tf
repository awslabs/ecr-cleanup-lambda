variable "DRYRUN" {
  default = true
}

variable "IMAGES_TO_KEEP" {
  default = 50
}

variable "IGNORE_TAGS_REGEX" {
  default = "release|archive"
}

variable "NAME_OF_FUNCTION" {
  default = "ecr-cleanup-lambda"
}

variable "REGION" {
  default = "None"
}

variable "ECR_REPOS_LIFECYCLE" {
  default = "alpine,apache"
}