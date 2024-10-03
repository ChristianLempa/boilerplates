# CIVO Provider
# ---
# Initial Provider Configuration for CIVO

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    civo = {
      source = "civo/civo"
      version = "~> 1.1.0"
    }
  }
}

provider "civo" {
    token = var.civo_token
    # (optional): Specify your region
    # region = "FRA1"
}
