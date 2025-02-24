# Cloudflare DNS
# ---
# Templates to manage DNS Records on Cloudflare

# A Record
resource "cloudflare_record" "your-dns-record-name" {
    for_each = var.dns_record_name
    zone_id = vR.cloudflare_zone_id
    name = each.value.name
    value = each.value.value
    type = each.value.type
    ttl = each.value.ttl
    proxied = each.value.proxied  # set to true, to hide public IP
}
