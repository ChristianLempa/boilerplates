# Ubuntu Server Focal Docker
# ---
# Packer Template to create an Ubuntu Server (Focal) with Docker on Proxmox

# Variable Definitions
variable "proxmox_api_url" {
    type = string
}

variable "proxmox_api_token_id" {
    type = string
}

variable "proxmox_api_token_secret" {
    type      = string
    sensitive = true
}

locals {
    disk_storage = "local-lvm"
}

# Resource Definiation for the VM Template
source "proxmox" "ubuntu-server-focal-docker" {

    # Proxmox Connection Settings
    proxmox_url = "${var.proxmox_api_url}"
    username    = "${var.proxmox_api_token_id}"
    token       = "${var.proxmox_api_token_secret}"
    # (Optional) Skip TLS Verification
    # insecure_skip_tls_verify = true

    # VM General Settings
    node                 = "your-proxmox-node"
    vm_id                = "100"
    vm_name              = "ubuntu-server-focal-docker"
    template_description = "Ubuntu Server Focal Image with Docker pre-installed"

    # VM OS Settings
    # (Option 1) Local ISO File
    # boot_iso {
    #     type         = "scsi"
    #     iso_file     = "local:iso/ubuntu-20.04.2-live-server-amd64.iso"
    #     unmount      = true
    #     iso_checksum = "f8e3086f3cea0fb3fefb29937ab5ed9d19e767079633960ccb50e76153effc98"
    # }
    # (Option 2) Download ISO
    # boot_iso {
    #     type             = "scsi"
    #     iso_url          = "https://releases.ubuntu.com/20.04/ubuntu-20.04.3-live-server-amd64.iso"
    #     unmount          = true
    #     iso_storage_pool = "local"
    #     iso_checksum     = "file:https://releases.ubuntu.com/focal/SHA256SUMS"
    # }

    # VM System Settings
    qemu_agent = true

    # VM Hard Disk Settings
    scsi_controller = "virtio-scsi-pci"

    disks {
        disk_size         = "25G"
        format            = "qcow2"
        storage_pool      = ${local.disk_storage}
        type              = "virtio"
    }

    # VM CPU Settings
    cores = "1"

    # VM Memory Settings
    memory = "2048"

    # VM Network Settings
    network_adapters {
        model    = "virtio"
        bridge   = "vmbr0"
        firewall = "false"
    }

    # VM Cloud-Init Settings
    cloud_init              = true
    cloud_init_storage_pool = ${local.disk_storage}

    # PACKER Boot Commands
    boot         = "c"
    boot_wait    = "5s"
    boot_command = [
        "<esc><wait><esc><wait>",
        "<f6><wait><esc><wait>",
        "<bs><bs><bs><bs><bs>",
        "autoinstall ds=nocloud-net;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/ ",
        "--- <enter>"
    ]
    # Useful for debugging
    # Sometimes lag will require this
    # boot_key_interval = "500ms"

    # PACKER Autoinstall Settings
    http_directory = "http"
    # (Optional) Bind IP Address and Port
    # http_bind_address = "0.0.0.0"
    # http_port_min     = 8802
    # http_port_max     = 8802

    ssh_username = "your-user-name"

    # (Option 1) Add your Password here
    # ssh_password = "your-password"
    # - or -
    # (Option 2) Add your Private SSH KEY file here
    # ssh_private_key_file = "~/.ssh/id_rsa"

    # Raise the timeout, when installation takes longer
    ssh_timeout = "20m"
}

# Build Definition to create the VM Template
build {

    name = "ubuntu-server-focal-docker"
    sources = ["source.proxmox.ubuntu-server-focal-docker"]

    # Provisioning the VM Template for Cloud-Init Integration in Proxmox #1
    provisioner "shell" {
        inline = [
            "while [ ! -f /var/lib/cloud/instance/boot-finished ]; do echo 'Waiting for cloud-init...'; sleep 1; done",
            "sudo rm /etc/ssh/ssh_host_*",
            "sudo truncate -s 0 /etc/machine-id",
            "sudo apt -y autoremove --purge",
            "sudo apt -y clean",
            "sudo apt -y autoclean",
            "sudo cloud-init clean",
            "sudo rm -f /etc/cloud/cloud.cfg.d/subiquity-disable-cloudinit-networking.cfg",
            "sudo sync"
        ]
    }

    # Provisioning the VM Template for Cloud-Init Integration in Proxmox #2
    provisioner "file" {
        source      = "files/99-pve.cfg"
        destination = "/tmp/99-pve.cfg"
    }

    # Provisioning the VM Template for Cloud-Init Integration in Proxmox #3
    provisioner "shell" {
        inline = [ "sudo cp /tmp/99-pve.cfg /etc/cloud/cloud.cfg.d/99-pve.cfg" ]
    }

    # Provisioning the VM Template with Docker Installation #4
    provisioner "shell" {
        inline = [
            "sudo apt-get install -y ca-certificates curl gnupg lsb-release",
            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg",
            "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
            "sudo apt-get -y update",
            "sudo apt-get install -y docker-ce docker-ce-cli containerd.io"
        ]
    }
}
