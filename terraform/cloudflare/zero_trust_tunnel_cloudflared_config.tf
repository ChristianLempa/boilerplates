resource "cloudflare_zero_trust_tunnel_cloudflared_config" "example_tunnel_config" {
  account_id  = data.cloudflare_account.example_account.account_id
  tunnel_id   = data.cloudflare_zero_trust_tunnel_cloudflared.example_tunnel.tunnel_id
  config      = {
    ingress = [
      {
        hostname        = "replace-with-your-hostname"
        service         = "https://replace-with-your-service-url"
        origin_request  = {
          no_tls_verify = true
        }
      },
      {
        # Catch-all rule: This will match any other requests
        service = "http_status:404"
      }
    ]
  }
}
