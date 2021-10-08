# For more information, see https://www.terraform.io/docs/backends/types/remote.html
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

provider "cloudflare" {
    email = var.cloudflare_email
    api_key =  var.cloudflare_api_key
}