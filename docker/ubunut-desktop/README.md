# Ubuntu Desktop in Docker

## Overview

An example of a Dockerfile that can be used to create an image with Ubuntu desktop with installed :

- Visual Studio Code
- Python 3.10

Dockerfile

Copy code

```text
FROM ubuntu:20.04

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    software-properties-common \
    gnupg2 \
    wget

# Install Visual Studio Code
RUN wget -qO - https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main"
RUN apt-get update && apt-get install -y code

# Set Python 3.10 as the default Python version
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Set the working directory
WORKDIR /code

# Run Visual Studio Code
CMD ["code", "."]
```

You can then build the image using the following command:

Copy code

```bash
docker build -t <image-name> .
```

And run the container using the following command

bash
Copy code

```bash
docker run -it --rm -p 5901:5901 -v $(pwd):/code <image-name>
```

This will run the container in interactive mode, and forward the host's port 5901 to the container's port 5901 so that you can access the desktop environment using a VNC client. The -v option maps the current working directory on the host to the /app directory in the container, so any changes made to the files in that directory will be persisted on the host.