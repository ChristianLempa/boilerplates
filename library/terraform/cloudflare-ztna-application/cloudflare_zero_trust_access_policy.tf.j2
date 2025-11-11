{% if service_token_enabled %}
resource "cloudflare_zero_trust_access_policy" "{{ resource_name }}_service_token" {
  account_id       = data.cloudflare_account.main.account_id
  name             = "{{ service_token_policy_name }}"
  decision         = "non_identity"
  include          = [{
    service_token = {
      token_id = "{{ service_token_id }}"
    }
  }]
  session_duration = "{{ session_duration }}"
}
{% endif %}
{% if ip_policy_enabled %}
resource "cloudflare_zero_trust_access_policy" "{{ resource_name }}_ip" {
  account_id       = data.cloudflare_account.main.account_id
  name             = "{{ ip_policy_name }}"
  decision         = "non_identity"
  include          = [
{% for ip_range in ip_ranges.split(',') %}
    {
      ip = {
        ip = "{{ ip_range.strip() }}"
      }
    }{{ "," if not loop.last else "" }}
{% endfor %}
  ]
  session_duration = "{{ session_duration }}"
}
{% endif %}
