# Installation

## Deployment

Copy the `docker-compose.yml` template into your project folder and start the container.

## Configuration

Visit the Nginxproxymanager Web Interface `http://localhost:81`, and login with Nginxproxymanager's default username `admin@example.com` and password: `changeme`.

*For more info visit:* [Official Nginxproxymanager Installation Documentation](https://nginxproxymanager.com/guide/)

# Best-Practices & Post-Installation

## Disable HTTP

It's not secure to expose Nginxproxymanager via the HTTP protocol. Follow these steps to enable HTTPS only.

### Don't expose Nginxproxymanager's UI on port 81

- [ ] Add a Proxy Host for Nginxproxymanager's WebUI to target `127.0.0.1:81`
- [ ] Remove port `:81` from the `docker-compose` file


# Additional Referfences

[Official Nginxproxymanager Installation Documentation](https://nginxproxymanager.com/guide/)