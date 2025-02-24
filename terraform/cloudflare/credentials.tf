# Cloudflare Credentials
# ---
# Credential Variables needed for Cloudflare

# Cloudflare Config
variable "cloudflare_email" {
    description = "The email address for your Cloudflare account"
    type = string
}
variable "cloudflare_api_key" {
    description = "The API key for your Cloudflare account"
    type = string
}
variable "cloudflare_zone_id" {
    description = "The Zone ID for your Cloudflare account"
    type = string
}
variable "dns_record_name" {
    description = "The name of the DNS record you want to create"
    type = map(string)
    default = {
        ubuntu  = {
            name = "ubuntu"
            value = "192.168.68.65:8080"
            type = "A"
            ttl = 1
            proxied = true
        }
        jellyfyn  = {
            name = "jellyfyn"
            value = ""
            type = "A"
            ttl = 1
            proxied = true
        }            
    }
}