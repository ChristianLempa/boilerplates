# [linuxserver.io](https.linuxserver.io)

[Blog] [Discord] [Discourse] [Fleet GitHub] [Open Collective]

The LinuxServer.io team brings you another container release featuring:

regular and timely application updates
easy user mappings (PGID, PUID)
custom base image with s6 overlay
weekly base OS updates with common layers across the entire LinuxServer.io ecosystem to minimise space usage, down time and bandwidth
regular security updates
Find us at:

Blog - all the things you can do with our containers including How-To guides, opinions and much more!
Discord - realtime support / chat with the community and the team.
Discourse - post on our community forum.
Fleet - an online web interface which displays all of our maintained images.
GitHub - view the source for all of our repositories.
Open Collective - please consider helping us by either donating or contributing to our budget
linuxserver/kasm
Scarf.io pulls GitHub Stars GitHub Release GitHub Package Repository GitLab Container Registry Quay.io Docker Pulls Docker Stars Jenkins Build LSIO CI

Kasm Workspaces is a docker container streaming platform for delivering browser-based access to desktops, applications, and web services. Kasm uses devops-enabled Containerized Desktop Infrastructure (CDI) to create on-demand, disposable, docker containers that are accessible via web browser. Example use-cases include Remote Browser Isolation (RBI), Data Loss Prevention (DLP), Desktop as a Service (DaaS), Secure Remote Access Services (RAS), and Open Source Intelligence (OSINT) collections.

The rendering of the graphical-based containers is powered by the open-source project KasmVNC.

kasm

Supported Architectures
We utilise the docker manifest for multi-platform awareness. More information is available from docker here and our announcement here.

Simply pulling lscr.io/linuxserver/kasm:latest should retrieve the correct image for your arch, but you can also pull specific arch images via tags.

The architectures supported by this image are:

Architecture	Available	Tag
x86-64	✅	amd64-<version tag>
arm64	✅	arm64v8-<version tag>
armhf	❌	
Version Tags
This image provides various versions that are available via tags. Please read the descriptions carefully and exercise caution when using unstable or development tags.

Tag	Available	Description
latest	✅	Stable Kasm releases
develop	✅	Tip of develop
Application Setup
This container uses Docker in Docker and requires being run in privileged mode. This container also requires an initial setup that runs on port 3000.

Unlike other containers the web interface port (default 443) needs to be set for the env variable KASM_PORT and both the inside and outside port IE for 4443 KASM_PORT=4443 -p 4443:4443

Unraid users due to the DinD storage layer /opt/ should be mounted directly to a disk IE /mnt/disk1/appdata/path or optimally with a cache disk at /mnt/cache/appdata/path

Access the installation wizard at https://your ip:3000 and follow the instructions there. Once setup is complete access https://your ip:443 and login with the credentials you entered during setup. The default users are:

admin@kasm.local
user@kasm.local
Currently Synology systems are not supported due to them blocking CPU scheduling in their Kernel.

GPU Support
During installation an option will be presented to force all Workspace containers to mount in and use a specific GPU. If using an NVIDIA GPU you will need to pass -e NVIDIA_VISIBLE_DEVICES=all or --gpus all and have the NVIDIA Container Runtime installed on the host. Also if using NVIDIA, Kasm Workspaces has native NVIDIA support so you can optionally opt to simply use that instead of he manual override during installation.

Gamepad support
In order to properly create virtual Gamepads you will need to mount from your host /dev/input and /run/udev/data. Please see HERE for instructions on enabling gamepad support.

Persistant profiles
In order to use persistant profiles in Workspaces you will need to mount in a folder to use from your host to /profiles. From there when configuring a workspace you can set the Persistant Profile Path to IE /profiles/ubuntu-focal/{username}/, more infomation can be found HERE.

Usage
Here are some example snippets to help you get started creating a container.

docker-compose (recommended, click here for more info)
---
version: "2.1"
services:
  kasm:
    image: lscr.io/linuxserver/kasm:latest
    container_name: kasm
    privileged: true
    environment:
      - KASM_PORT=443
      - TZ=Europe/London
      - DOCKER_HUB_USERNAME=USER #optional
      - DOCKER_HUB_PASSWORD=PASS #optional
    volumes:
      - /path/to/data:/opt
      - /path/to/profiles:/profiles #optional
      - /dev/input:/dev/input #optional
      - /run/udev/data:/run/udev/data #optional
    ports:
      - 3000:3000
      - 443:443
    restart: unless-stopped
docker cli (click here for more info)
docker run -d \
  --name=kasm \
  --privileged \
  -e KASM_PORT=443 \
  -e TZ=Europe/London \
  -e DOCKER_HUB_USERNAME=USER `#optional` \
  -e DOCKER_HUB_PASSWORD=PASS `#optional` \
  -p 3000:3000 \
  -p 443:443 \
  -v /path/to/data:/opt \
  -v /path/to/profiles:/profiles `#optional` \
  -v /dev/input:/dev/input `#optional` \
  -v /run/udev/data:/run/udev/data `#optional` \
  --restart unless-stopped \
  lscr.io/linuxserver/kasm:latest
Parameters
Container images are configured using parameters passed at runtime (such as those above). These parameters are separated by a colon and indicate <external>:<internal> respectively. For example, -p 8080:80 would expose port 80 from inside the container to be accessible from the host's IP on port 8080 outside the container.

Parameter	Function
-p 3000	Kasm Installation wizard. (https)
-p 443	Kasm Workspaces interface. (https)
-e KASM_PORT=443	Specify the port you bind to the outside for Kasm Workspaces.
-e TZ=Europe/London	Specify a timezone to use EG Europe/London.
-e DOCKER_HUB_USERNAME=USER	Optionally specify a DockerHub Username to pull private images.
-e DOCKER_HUB_PASSWORD=PASS	Optionally specify a DockerHub password to pull private images.
-v /opt	Docker and installation storage.
-v /profiles	Optionally specify a path for persistent profile storage.
-v /dev/input	Optional for gamepad support.
-v /run/udev/data	Optional for gamepad support.
Environment variables from files (Docker secrets)
You can set any environment variable from a file by using a special prepend FILE__.

As an example:

-e FILE__PASSWORD=/run/secrets/mysecretpassword
Will set the environment variable PASSWORD based on the contents of the /run/secrets/mysecretpassword file.

Umask for running applications
For all of our images we provide the ability to override the default umask settings for services started within the containers using the optional -e UMASK=022 setting. Keep in mind umask is not chmod it subtracts from permissions based on it's value it does not add. Please read up here before asking for support.

Docker Mods
Docker Mods Docker Universal Mods

We publish various Docker Mods to enable additional functionality within the containers. The list of Mods available for this image (if any) as well as universal mods that can be applied to any one of our images can be accessed via the dynamic badges above.

Support Info
Shell access whilst the container is running: docker exec -it kasm /bin/bash
To monitor the logs of the container in realtime: docker logs -f kasm
container version number
docker inspect -f '{{ index .Config.Labels "build_version" }}' kasm
image version number
docker inspect -f '{{ index .Config.Labels "build_version" }}' lscr.io/linuxserver/kasm:latest
Updating Info
Most of our images are static, versioned, and require an image update and container recreation to update the app inside. With some exceptions (ie. nextcloud, plex), we do not recommend or support updating apps inside the container. Please consult the Application Setup section above to see if it is recommended for the image.

Below are the instructions for updating containers:

Via Docker Compose
Update all images: docker-compose pull
or update a single image: docker-compose pull kasm
Let compose update all containers as necessary: docker-compose up -d
or update a single container: docker-compose up -d kasm
You can also remove the old dangling images: docker image prune
Via Docker Run
Update the image: docker pull lscr.io/linuxserver/kasm:latest
Stop the running container: docker stop kasm
Delete the container: docker rm kasm
Recreate a new container with the same docker run parameters as instructed above (if mapped correctly to a host folder, your /config folder and settings will be preserved)
You can also remove the old dangling images: docker image prune
Via Watchtower auto-updater (only use if you don't remember the original parameters)
Pull the latest image at its tag and replace it with the same env variables in one run:

docker run --rm \
-v /var/run/docker.sock:/var/run/docker.sock \
containrrr/watchtower \
--run-once kasm
You can also remove the old dangling images: docker image prune

Note: We do not endorse the use of Watchtower as a solution to automated updates of existing Docker containers. In fact we generally discourage automated updates. However, this is a useful tool for one-time manual updates of containers where you have forgotten the original parameters. In the long term, we highly recommend using Docker Compose.

Image Update Notifications - Diun (Docker Image Update Notifier)
We recommend Diun for update notifications. Other tools that automatically update containers unattended are not recommended or supported.
Building locally
If you want to make local modifications to these images for development purposes or just to customize the logic:

git clone https://github.com/linuxserver/docker-kasm.git
cd docker-kasm
docker build \
  --no-cache \
  --pull \
  -t lscr.io/linuxserver/kasm:latest .
The ARM variants can be built on x86_64 hardware using multiarch/qemu-user-static

docker run --rm --privileged multiarch/qemu-user-static:register --reset
Once registered you can define the dockerfile to use with -f Dockerfile.aarch64.

Versions
05.11.22: - Rebase to Jammy, add support for GPUs, add support for Gamepads.
23.09.22: - Migrate to s6v3.
02.07.22: - Initial Release.