### [image Bind9 | Ubuntu ](https://hub.docker.com/r/ubuntu/bind9)

if you are running it on an ubuntu machine first you have to disable `Network Name Resolution` service

```bash
vim /etc/systemd/resolved.conf
```

change `#DNSStubListener=yes` to `DNSStubListener=no` and restart its service

```bash
sudo systemctl restart systemd-resolved.service
```

create following directories and give write access to other users to `cache` directory

```bash
mkdir ./config ./cache ./records && chmod o+w ./cache
```

change your Domain configurations in `./config/named.conf` file

start `Bind` service with:

```bash
sudo docker compose up -d
```
