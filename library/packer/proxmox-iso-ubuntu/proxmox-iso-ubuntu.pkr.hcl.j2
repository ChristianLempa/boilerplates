# Ubuntu Server Noble (24.04.x)
# ---
# Packer Template to create an Ubuntu Server (Noble 24.04.x) on Proxmox

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
    disk_storage = "{{ disk_storage }}"
}

# Resource Definition for the VM Template
source "proxmox-iso" "{{ image_name }}" {

    # Proxmox Connection Settings
    proxmox_url = "${var.proxmox_api_url}"
    username    = "${var.proxmox_api_token_id}"
    token       = "${var.proxmox_api_token_secret}"
{% if skip_tls_verify %}
    # Skip TLS Verification
    insecure_skip_tls_verify = true
{% endif %}

    # VM General Settings
    node                 = "{{ proxmox_node }}"
    vm_id                = "{{ vm_id }}"
    vm_name              = "{{ image_name }}"
    template_description = "{{ vm_description }}"

    # VM OS Settings
{% if iso_source == "local" %}
    # Local ISO File
    boot_iso {
        type         = "scsi"
        iso_file     = "{{ iso_file }}"
        unmount      = true
        iso_checksum = "{{ iso_checksum }}"
    }
{% elif iso_source == "download" %}
    # Download ISO
    boot_iso {
        type             = "scsi"
        iso_url          = "{{ iso_url }}"
        unmount          = true
        iso_storage_pool = "{{ iso_storage }}"
        iso_checksum     = "{{ iso_checksum }}"
    }
{% endif %}

    # VM System Settings
    qemu_agent = true

    # VM Hard Disk Settings
    scsi_controller = "virtio-scsi-pci"

    disks {
        disk_size         = "{{ disk_size }}"
        format            = "qcow2"
        storage_pool      = local.disk_storage
        type              = "virtio"
    }

    # VM CPU Settings
    cores = "{{ cpu_cores }}"

    # VM Memory Settings
    memory = "{{ memory_mb }}"

    # VM Network Settings
    network_adapters {
        model    = "virtio"
        bridge   = "{{ network_bridge }}"
        firewall = "false"
    }

    # VM Cloud-Init Settings
    cloud_init              = true
    cloud_init_storage_pool = "{{ cloudinit_storage }}"

    # PACKER Boot Commands
    boot         = "c"
    boot_wait    = "{{ boot_wait }}"
    communicator = "ssh"
    boot_command = [
        "<esc><wait>",
        "e<wait>",
        "<down><down><down><end>",
        "<bs><bs><bs><bs><wait>",
        "autoinstall ds=nocloud-net\\\\;s=http://{{ '{{ .HTTPIP }}' }}:{{ '{{ .HTTPPort }}' }}/ ---<wait>",
        "<f10><wait>"
    ]

    # PACKER Autoinstall Settings
    http_directory    = "http"
    http_bind_address = "{{ http_bind_address }}"
    http_port_min     = {{ http_port_min }}
    http_port_max     = {{ http_port_max }}

    ssh_username = "{{ ssh_username }}"

{% if ssh_auth_method == "password" %}
    # SSH Password Authentication
    ssh_password = "{{ ssh_password }}"
{% elif ssh_auth_method == "key" %}
    # SSH Key Authentication
    ssh_private_key_file = "{{ ssh_private_key_file }}"
{% endif %}

    # Raise the timeout, when installation takes longer
    ssh_timeout = "{{ ssh_timeout }}"
    ssh_pty     = true
}

# Build Definition to create the VM Template
build {

    name    = "{{ image_name }}"
    sources = ["source.proxmox-iso.{{ image_name }}"]

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
            "sudo rm -f /etc/netplan/00-installer-config.yaml",
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

    # Add additional provisioning scripts here
    # ...
}
