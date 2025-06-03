# Packer Proxmox

You can add an additional description here.

## Installing Proxmox plugin
You have two options:
- You can add this config block to your pkr.hcl file and run ```packer init```.

```
packer {
  required_plugins {
    name = {
      version = "~> 1"
      source  = "github.com/hashicorp/proxmox"
    }
  }
}
```

- Run ```packer plugins install github.com/hashicorp/proxmox``` to install the plugin globally in packer.

## Running Packer

1. Navigate into the folder you want to create a template with
2. Run ```packer build -var-file ../credentials.pkr.hcl .```


## Troubleshooting 
- If you have tailscale installed, be aware that packer could grab the IP of your tailscale adapter rather than your LAN. You can either hard code the IP in the boot command or try setting the ```http_interface``` option
- Sometimes the boot command is typed too fast and can cause issues. You can increase the time between types by using the ```boot_key_interval``` option.

