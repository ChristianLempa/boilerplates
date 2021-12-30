# Installing


# Customization

## Data Persistence
... Storing Data in the `/etc/traefik` directory on the host, passing through...
```yaml
    volumes:
      - /etc/traefik:/etc/traefik
```

## Self-Signed Certificates
According to traefik's documentation it will automatically generate self-signed Certificates if no Default Certificate is provided. If you'd like to overwrite the self-signed Certificate with your own, uncomment the section for 
```yaml 
# (Optional) Overwrite Default Certificates
tls:
  stores:
    default:
      defaultCertificate:
        certFile: /etc/traefik/certs/cert.pem
        keyFile: /etc/traefik/certs/cert-key.pem
```
Replace the `/etc/traefik/certs/cert.pem` with your certificate file, and the `/etc/traefik/certs/cert-key.pem` with your certificate key.


# Best-Practices

```yaml
providers:
  docker:
    exposedByDefault: false  # Default is true
  file:
    # watch for dynamic configuration changes
    directory: /etc/traefik
    watch: true
```