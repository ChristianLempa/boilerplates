# Installing

## Manage local environment

Allows Portainer to manage the local Docker Environment

```yaml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

## Data Persistence

Storing Data in a `portainer-data` volume on docker

```yaml
    volumes:
      - portainer-data:/data
```

# Best-Practices

### (Option 1): Upload custom certificates

- [ ] Upload your custom certificates
- [ ] Force HTTPS only
- [ ] Expose Port `9443`

![Force HTTPS Only and Certificates](https://imagedelivery.net/yG07CmQlapjZ95zez0HJMA/5cf8fa46-d548-4f0b-570e-0caf8ee6d700/medium)


### (Option 2): Use a Reverse Proxy

Use a Reverse Proxy to securely expose administrative services.
