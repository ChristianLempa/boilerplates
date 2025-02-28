terraform {
  required_version = ">= 0.13.0"

  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
      version = "~> 5.0.0"
    }
  }
}

variable "CLOUDFLARE_TOKEN" {
  type      = string
  sensitive = true
}

provider "cloudflare" {
  api_token = var.CLOUDFLARE_TOKEN
}
