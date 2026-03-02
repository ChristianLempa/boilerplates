resource "dns_a_record_set" "{{ dns_hostname }}_record" {
  zone = "{{ dns_zone }}"
  name = "{{ dns_hostname }}"
  addresses = [
    "{{ ip_address }}"
  ]
  ttl = "{{ dns_ttl | default('3600') }}"
}
