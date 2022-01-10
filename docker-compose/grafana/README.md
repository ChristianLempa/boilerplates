# Installation

## Deployment

Copy the `docker-compose.yml` template into your project folder and start the container.

## Configuration

Visit the Grafana Web Interface `http://localhost:3000`, and login with Grafana's default username and password: `admin`.

*For more info visit:* [Official Grafana Getting started Documentation](https://grafana.com/docs/grafana/latest/getting-started/getting-started/)

# Best-Practices & Post-Installation

## Disable HTTP

It's not secure to expose Grafana via the HTTP protocol. 

### Use a Reverse Proxy

- [ ] Use a Reverse Proxy to securely expose administrative services.

# Additional Referfences

[Official Grafana Documentation](https://grafana.com/docs/grafana/latest/)