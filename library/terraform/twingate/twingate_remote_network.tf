data "twingate_remote_network" "default_network" {
  name = "default_network"
}

resource "twingate_remote_network" "new_network" {
  name = "new_network"
}
