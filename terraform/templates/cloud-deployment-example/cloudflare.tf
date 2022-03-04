variable "zone_id" {}

resource "cloudflare_record" "server" {
  zone_id = var.zone_id
  name    = "your-dns-name"
  value   = civo_instance.server.public_ip
  type    = "A"
  proxied = false
}
