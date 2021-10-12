# General Terraform Settings
# ---

terraform {
  required_providers {
    cloudflare = {
        source = "cloudflare/cloudflare"
        version = "~> 3.0"
    }
    civo = {
        source = "civo/civo"
    }
  }
}

# Declare Variables
# ---
# TODO: Create a yourfile.auto.tfvars file in the project directory and add your variables in it.
#   Example:
#   cloudflare_email = "youremail@yourmail.com"
#   cloudflare_api_key = "your-api-key"
#   civo_token = "your-token"

variable "cloudflare_email" {}
variable "cloudflare_api_key" {}
variable "civo_token" {}

# Set Default Provider Settings
# ---

provider "cloudflare" {
  email = var.cloudflare_email
  api_key =  var.cloudflare_api_key
}

provider "civo" {
  token = var.civo_token
  # (optional) change the defaullt region
  # region = "FRA1"
}