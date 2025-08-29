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
