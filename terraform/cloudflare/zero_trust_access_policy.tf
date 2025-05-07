resource "cloudflare_zero_trust_access_policy" "example_policy" {
  account_id  = data.cloudflare_account.example_account.account_id
  name        = "example_policy"
  decision    = "allow"
  include     = [
    {
      ip = {
        ip = "replace-with-your-ip-address"
      }
    }
  ]
}
