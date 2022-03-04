# Cloudflare DNS
# ---
# Templates to manage DNS Records on Cloudflare

# A Record
resource "cloudflare_record" "your-dns-record-name" {
    zone_id = "your-zone-id"
    name = "your-public-dns-value"
    value =  "your-public-ip-address"
    type = "A"
    proxied = false  # set to true, to hide public IP
}
