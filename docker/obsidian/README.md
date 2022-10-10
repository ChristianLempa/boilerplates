# Quick Start
After the container starts use http://IP_OF_DOCKER_HOST:8080 to access. http://127.0.0.1:8080 12 if local.

## Bash
'''
docker run --rm -it \
  -v /pathonhosttostoreyour/vaults:/vaults \
  -v /pathonhosttostoreinternalobsidian/config:/config \
  -p 8080:8080 \
  ghcr.io/sytone/obsidian-remote:latest
'''

## PowerShell
'''
docker run --rm -it `
  -v D:/ob/vaults:/vaults `
  -v D:/ob/config:/config `
  -p 8080:8080 `
  ghcr.io/sytone/obsidian-remote:latest
'''

## Latest Release: Obsidian Remote v0.0.3
Updated menu so you can reopen Obsidian after closing it in the browser.
Added clip showing close and restart of Obsidian in browser
Format cleanup
Full Changelog: v0.0.2…v0.0.3 21
Source: sytone/obsidian-remote: Run Obsidian.md in a browser via a docker container. (github.com) 243

##reference:
[https://forum.obsidian.md/t/self-hosted-docker-instance/3788/9](Original Thread 35)