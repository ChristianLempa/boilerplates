# CIVO Provider
# ---
# Initial Provider Configuration for CIVO

terraform {
  required_version = ">= 0.13.0"

  required_providers {
    civo = {
      source = "civo/civo"
      version = "~> 1.0.9"
    }
  }
}

provider "civo" {
    token = var.civo_token
    # (optional): Specify your region
    # region = "FRA1"
}
