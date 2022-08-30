# Teleport Boilerplates

//TODO Add Description

Tested with teleport 10

## Deployment

Copy the `docker-compose.yml`, and `config/teleport.yml` files into your project folder and start the container.

## Configuration

### Create a new user

```bash

```

## Best-Practices & Post-Installation

### Enable passwordless

To enable passwordless feature remove the **(Optional) Passwordless Authentication** statements from the `config/teleport.yml` file and re-start the container.

### Get a trusted SSL cert from Letsencrypt

To get a trusted SSL cert from Letsnecrypt remove the **(Optional) ACME** statements from the `config/teleport.yml` file and re-start the container.

*Note, you need a public DNS Record that points to your-server-url.*