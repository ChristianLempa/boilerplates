terraform {
  required_version = ">= 0.13.0"
  required_providers {
    twingate = {
      source = "Twingate/twingate"
      version = "3.5.0"
    }
  }
}

variable "TWINGATE_TOKEN" {
  type        = string
  description = "Twingate API Token"
  sensitive   = true
}

provider "twingate" {
  api_token = var.TWINGATE_TOKEN
  network   = ""  # FIXME Add your Twingate network name here
}
