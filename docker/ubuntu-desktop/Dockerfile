FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive

# Installing build dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y apt-utils 
RUN apt-get update && apt-get install -y build-essential automake make cmake g++ wget git mercurial python3-pip curl

# Preparing Python build environment
RUN pip3 install cython future scipy nltk requests xmltodict nose2

# Prepare environment UTF-8
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Update and install dependencies
RUN apt-get install -y python3.8 \
    python3-venv \
    software-properties-common \
    gnupg2 \
    wget

# Install Visual Studio Code
RUN wget -qO - https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main"
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y code

RUN apt-get clean

# Set Python 3.8 as the default Python version
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

# Set the working directory
WORKDIR /code

# Run Visual Studio Code
CMD ["code", "."]