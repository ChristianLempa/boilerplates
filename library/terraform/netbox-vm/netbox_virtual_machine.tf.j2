data "netbox_cluster" "{{ resource_name }}_cluster" {
  name = "{{ cluster_ref }}"
}

data "netbox_site" "{{ resource_name }}_site" {
  name = "{{ site_ref }}"
}

resource "netbox_virtual_machine" "{{ resource_name }}" {
  name       = "{{ vm_name }}"
  cluster_id = data.netbox_cluster.{{ resource_name }}_cluster.id
{% if site_ref %}
  site_id    = data.netbox_site.{{ resource_name }}_site.id
{% endif %}
  status     = "{{ status }}"
{% if device_ref %}
  device_id  = netbox_device.{{ device_ref }}.id
{% endif %}
{% if resources_enabled %}
  vcpus      = {{ vcpus }}
  memory     = {{ memory_mb }}
  disk       = {{ disk_gb }}
{% endif %}
{% if description_enabled %}
  comments   = "{{ description_text }}"
{% endif %}
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

{% if ipam_enabled %}
resource "netbox_interface" "{{ resource_name }}_interface" {
  name               = "{{ interface_name }}"
  virtual_machine_id = netbox_virtual_machine.{{ resource_name }}.id
}

resource "netbox_ip_address" "{{ resource_name }}_ip" {
  ip_address   = "{{ primary_ip4 }}"
  status       = "active"
  {% if dns_name %}
  dns_name     = "{{ dns_name }}"
  {% endif %}
  interface_id = netbox_interface.{{ resource_name }}_interface.id
  object_type  = "virtualization.vminterface"
}

resource "netbox_primary_ip" "{{ resource_name }}_primary_ip" {
  ip_address_id      = netbox_ip_address.{{ resource_name }}_ip.id
  virtual_machine_id = netbox_virtual_machine.{{ resource_name }}.id
}
{% endif %}
