data "civo_ssh_key" "sshkey" {
  name = "your-ssh-key-name"
}

resource "civo_instance" "server" {
    hostname = "servername"
    size = "g3.small"
    disk_image = "ubuntu-focal"
    # (optional):
    # ---
    # tags = ["python", "nginx"]
    # notes = "this is a note for the server"
    # initial_user = "user"
    # sshkey_id = data.civo_ssh_key.sshkey.id
}