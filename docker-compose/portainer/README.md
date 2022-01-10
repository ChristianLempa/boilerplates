# Installation

## Deployment

1. Copy the `docker-compose.yml` template into your project folder and start the container.

### Manage local environment

Allows Portainer to manage the local Docker Environment
```yaml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

### Data Persistence

Storing Data in a `portainer-data` volume on docker
```yaml
    volumes:
      - portainer-data:/data
```

## Configuration



# Best-Practices & Post-Installation

## Disable HTTP

It's not secure to expose Portainer via the HTTP protocol. Follow these steps to enable HTTPS only.

### (Option 1): Upload custom certificates

- [ ] Upload your custom certificates
- [ ] Force HTTPS only
- [ ] Expose Port `9443`
![Force HTTPS Only and Certificates](https://imagedelivery.net/yG07CmQlapjZ95zez0HJMA/5cf8fa46-d548-4f0b-570e-0caf8ee6d700/medium)

### (Option 2): Use a Reverse Proxy

- [ ] Use a Reverse Proxy to securely expose administrative services.

# Additional Referfences

[Official Portainer Documentation](https://docs.portainer.io/)
