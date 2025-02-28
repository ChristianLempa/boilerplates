data "cloudflare_zero_trust_tunnel_cloudflared" "example_tunnel" {
  account_id  = data.cloudflare_account.example_account.account_id
  tunnel_id   = "replace-wiht-your-tunnel-id"
}
