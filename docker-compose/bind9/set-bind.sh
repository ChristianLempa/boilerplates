#!/bin/bash
# before running the docker image, run this script to set the
# uid to 100 and gid to 101. This is based on the bind user in the Ubuntu docker image
#:/# grep bind /etc/passwd
#bind:x:100:101::/var/cache/bind:/usr/sbin/nologin
#
chown 100:101 -R cache
chown 100:101 -R config
chown 100:101 -R records
chmod 775 cache
chmod 775 config
chmod 775 records
