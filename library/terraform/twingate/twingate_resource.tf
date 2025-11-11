resource "twingate_resource" "new_resource" {
  name                = "new_resource"
  address             = "new_resource.home.arpa"
  remote_network_id   = data.twingate_remote_network.default_network.id
  security_policy_id  = data.twingate_security_policy.default_policy.id

  protocols = {
    allow_icmp = true
    tcp = {
      policy = "ALLOW_ALL"
    }
    udp = {
      policy = "ALLOW_ALL"
    }
  }

  dynamic "access_group" {
    for_each = [
      twingate_group.administrators.id
    ]
    content {
      group_id = access_group.value
      security_policy_id = data.twingate_security_policy.default_policy.id
    }
  }

  is_active = true
}
