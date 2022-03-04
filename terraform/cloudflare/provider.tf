# Cloudflare Provider
# ---
# Initial Provider Configuration for Cloudflare

terraform {
  required_version = ">= 0.13.0"

  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
      version = "~> 3.0"
    }
  }
}

provider "cloudflare" {
    email = var.cloudflare_email
    api_key =  var.cloudflare_api_key
}
