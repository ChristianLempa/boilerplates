#!/bin/bash

# Ensure to run as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# Create the Bitwarden user
adduser bitwarden
passwd bitwarden

# Check if the docker group exists, create it if not
if ! getent group docker > /dev/null; then
    groupadd docker
fi

# Add the Bitwarden user to the docker group
usermod -aG docker bitwarden

# Create the Bitwarden data directory
mkdir /opt/bitwarden

# Set the permissions on the Bitwarden data directory
chmod -R 700 /opt/bitwarden

# And ownership 
chown -R bitwarden:bitwarden /opt/bitwarden

su - bitwarden -c "bash $(pwd)/post-install-2.sh"