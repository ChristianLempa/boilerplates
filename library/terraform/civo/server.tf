# CIVO Servers
# ---
# Templates to create a Linux Server on CIVO

# CIVO Instance Server
resource "civo_instance" "your-server" {
    hostname = "your-fqdn-server-name"
    size = data.civo_size.instance_xsmall.sizes.0.name
    disk_image = data.civo_disk_image.debian.diskimages.0.id
    # initial_user = "your-initial-user"
    # sshkey_id = data.civo_ssh_key.your-ssh-key.id
    # reverse_dns = "your-server.your-domain"
}

