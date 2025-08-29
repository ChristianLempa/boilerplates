# CIVO SSH Keys
# ---
# Query or Create SSH Keys to authenticate to Servers on CIVO

# Query existing CIVO SSH Key
data "civo_ssh_key" "your-ssh-key" {
  name = "your-ssh-key-name"
}

# Create new SSH Key
resource "civo_ssh_key" "your-ssh-key"{
    name = "your-ssh-key-name"
    public_key = file("~/.ssh/id_rsa.pub")
}
