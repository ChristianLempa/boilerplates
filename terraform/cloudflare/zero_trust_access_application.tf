resource "cloudflare_zero_trust_access_application" "example_app" {
  zone_id           = data.cloudflare_zone.example.id
  name              = "example_app"
  domain            = "example_app.example.com"
  type              = "self_hosted"
  session_duration  = "30m"
  policies          = [
    {
      id          = cloudflare_zero_trust_access_policy.example_policy.id
      precedence  = 0
      decision    = "allow"
    }
  ]
}
