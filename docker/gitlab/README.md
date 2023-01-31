# Quick Start

After the container starts use http://IP_OF_DOCKER_HOST, https://IP_OF_DOCKER_HOST to access. 
SSH IP_OF_DOCKER_HOST .

## Bash

```bash
docker run --detach \
  --hostname gitlab.example.com \
  --env GITLAB_OMNIBUS_CONFIG="external_url 'http://my.domain.com/'; gitlab_rails['lfs_enabled'] = true;" \
  --publish 443:443 --publish 80:80 --publish 22:22 \
  --name gitlab \
  --restart always \
  --volume $GITLAB_HOME/config:/etc/gitlab \
  --volume $GITLAB_HOME/logs:/var/log/gitlab \
  --volume $GITLAB_HOME/data:/var/opt/gitlab \
  --shm-size 256m \
  gitlab/gitlab-ee:latest
```

## PowerShell

```powershell
docker run --detach \
  --hostname gitlab.example.com \
  --env GITLAB_OMNIBUS_CONFIG="external_url 'http://my.domain.com/'; gitlab_rails['lfs_enabled'] = true;" \
  --publish 443:443 --publish 80:80 --publish 22:22 \
  --name gitlab \
  --restart always \
  --volume $GITLAB_HOME/config:/etc/gitlab \
  --volume $GITLAB_HOME/logs:/var/log/gitlab \
  --volume $GITLAB_HOME/data:/var/opt/gitlab \
  --shm-size 256m \
  gitlab/gitlab-ee:latest
```

## Latest Release: Gitlab 15.8

Updated menu so you can reopen Obsidian after closing it in the browser.
Added clip showing close and restart of Obsidian in browser
Format cleanup
Full Changelog: v0.0.2…v0.0.3 21
Source: sytone/obsidian-remote: Run Obsidian.md in a browser via a docker container. (github.com) 243

## Reference :

[Gitlab docker install](https://docs.gitlab.com/ee/install/docker.html)