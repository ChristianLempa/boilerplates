# Installation

TODO: ...

# Best-Practices & Post-Installation

## Disable HTTP

It's not secure to expose InfluxDB via the HTTP protocol. Follow these steps to enable HTTPS only.

### (Option 1): Upload custom certificates

TODO: Not tested in Docker-Compose...

- [ ] Run the container with tls parameters
`influxd --tls-cert=/etc/ssl/cert.pem --tls-key=/etc/ssl/cert-key.pem`

### (Option 2): Use a Reverse Proxy

- [] Use a Reverse Proxy to securely expose administrative services.

# Additional Referfences

[Official InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2.1/)