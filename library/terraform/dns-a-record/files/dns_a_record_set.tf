resource "dns_a_record_set" "{{ resource_name }}" {
  zone      = "{{ zone }}"
  name      = "{{ record_name }}"
  addresses = [
    "{{ ip_address }}"{% if multiple_addresses and additional_ips %},
{% for ip in additional_ips.split(',') %}
    "{{ ip.strip() }}"{% if not loop.last %},{% endif %}

{% endfor %}
{% endif %}
  ]
  ttl       = {{ ttl }}
{% if depends_on_enabled %}
  depends_on = [{{ dependencies }}]
{% endif %}
{% if lifecycle_enabled %}

  lifecycle {
{% if prevent_destroy %}
    prevent_destroy = true
{% endif %}
{% if create_before_destroy %}
    create_before_destroy = true
{% endif %}
{% if ignore_changes %}
    ignore_changes = [{{ ignore_changes }}]
{% endif %}
  }
{% endif %}
}
