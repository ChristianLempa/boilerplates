# Installation

## Deployment

Copy the `docker-compose.yml` template into your project folder and start the container.

## Configuration

The initial configuration can be done automatically through docker instructions, or post-installation via the InfluxDB UI or CLI setup.

*For more info visit:* [Official InfluxDB Installation Documentation](https://docs.influxdata.com/influxdb/v2.1/install/)

# Best-Practices & Post-Installation

## Disable HTTP

It's not secure to expose InfluxDB via the HTTP protocol. Follow these steps to enable HTTPS only.

### (Option 1): Upload custom certificates

TODO: #15 Test Docker-Compose for InfluxDB2

- [ ] Run the container with tls parameters
`influxd --tls-cert=/etc/ssl/cert.pem --tls-key=/etc/ssl/cert-key.pem`

### (Option 2): Use a Reverse Proxy

- [ ] Use a Reverse Proxy to securely expose administrative services.

# Additional Referfences

[Official InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2.1/)