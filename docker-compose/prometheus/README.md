# Installation

## Deployment

1. Copy the configuration template into the `/etc/prometheus/prometheus.yml` location.
2. Copy the `docker-compose.yml` template into your project folder and start the container.

## Configuration

Configure your settings in the `/etc/prometheus/prometheus.yml` file.

*For more info visit:* [Official Prometheus Installation Documentation](https://prometheus.io/docs/prometheus/latest/installation/)

# Best-Practices & Post-Installation

## Disable HTTP

It's not secure to expose Prometheus via the HTTP protocol. 

### Use a Reverse Proxy

- [] Use a Reverse Proxy to securely expose administrative services.

# Additional Referfences

[Official Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)