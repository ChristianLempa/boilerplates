terraform {
  required_version = ">= 0.13.0"

  required_providers {
    dns = {
      source  = "hashicorp/dns"
      version = "3.5.0"
    }
  }
}

provider "dns" {
  update {
    server        = "{{ provider_server }}"
    key_name      = "tsig-key."
    key_algorithm = "hmac-sha256"
    key_secret    = "{{ provider_tsig_key_secret }}"
  }
}
