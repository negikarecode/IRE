variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "db_username" {
  type    = string
  default = "ire_master_admin"
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = "IRE_Super_Secure_Prod_Password_2026!"
}
