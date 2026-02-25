resource "cloudflare_dns_record" "{{ resource_name }}" {
  zone_id = data.cloudflare_zone.main.zone_id
  name    = "{{ name }}"
  content = "{{ content }}"
  type    = "{{ record_type }}"
  ttl     = {{ ttl }}
  proxied = {{ proxied | lower }}
{% if mx_enabled and record_type == "MX" %}
  priority = {{ priority }}
{% endif %}
{% if comment_enabled %}
  comment = "{{ comment_text }}"
{% endif %}
}
