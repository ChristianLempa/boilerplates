#!/bin/bash

# Ensure to run as bitwarden user
if [ "$(id -u)" != "$(id -u bitwarden)" ]; then
    echo "This script must be run as bitwarden user" 1>&2
    exit 1
fi
cd /opt/bitwarden

# Start the Bitwarden script
curl -Lso bitwarden.sh https://go.btwrdn.co/bw-sh && chmod 700 bitwarden.sh

./bitwarden.sh install

echo "At a minimum, you should replace the values for:
    ...
    globalSettings__mail__smtp__host=<placeholder>
    globalSettings__mail__smtp__port=<placeholder>
    globalSettings__mail__smtp__ssl=<placeholder>
    globalSettings__mail__smtp__username=<placeholder>
    globalSettings__mail__smtp__password=<placeholder>
    ...
    adminSettings__admins=
..."

nano ./bwdata/env/global.override.env

echo "Applying the changes to the Bitwarden environment file..."
./bitwarden.sh restart

echo "Change configs such as port"
nano ./bwdata/config.yml

echo "Rebuilding Bitwarden..."
./bitwarden.sh rebuild

# Ask if the user wants to start Bitwarden
echo "Do you want to start Bitwarden now? (y/n)"
read -r answer
if [ "$answer" = "y" ]; then
    ./bitwarden.sh start
fi

echo "Check if the Bitwarden docker service is running"
docker ps

echo "Check if the Bitwarden instance is working with your web domain"