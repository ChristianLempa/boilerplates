resource "cloudflare_record" "example.com" {
  zone_id = data.cloudflare_zone.example_zone.zone_id
  name    = "example"
  content = "content"
  type    = "A"
  proxied = true
  ttl     = 3600
}
