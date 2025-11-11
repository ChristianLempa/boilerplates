resource "civo_firewall" "your_firewall" {
  name       = "your-firewall-name"
  network_id = civo_network.your_network.id
  create_default_rules = true
}
