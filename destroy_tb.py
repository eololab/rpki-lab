#!/usr/bin/env python3
 
import sys
import pylxd
import random
import string
import urllib
import os
import docker

if len(sys.argv) != 2:
    print("Usage:",sys.argv[0],"<test-bed name>")
    sys.exit(1)

if os.geteuid() != 0:
    print("You need root permissions to set-up your test-bed")
    sys.exit(1)


# ID of the tb
TB_NAME = sys.argv[1]
 
# Create a lxd_client and a docker_client
lxd_client = pylxd.Client()
docker_client = docker.from_env()
 
# Delete all containers matching the name
# LXD
for cont in lxd_client.containers.all():
    if TB_NAME in cont.name:
        print("Stopping container {}".format(cont.name))
        cont.stop(wait=True)
        print("Deleting container {}".format(cont.name))
        cont.delete(wait=True)
# Docker
for cont in docker_client.containers.list():
    if TB_NAME in cont.name:
        print("Stopping container {}".format(cont.name))
        cont.stop()
print("Deleting all stopped docker containers")
docker_client.containers.prune()

# Delete the image we created for this TB
for image in lxd_client.images.all():
    if len([TB_NAME in alias['name'] for alias in image.aliases]) > 0:
        print("Deleting image {}".format(image.aliases[0]['name']))
        image.delete(wait=True)

# Delete the profile we created for this TB
for profile in lxd_client.profiles.all():
    if TB_NAME in profile.name:
        print("Deleting profile {}".format(profile.name))
        profile.delete(wait=True)

# Delete the storage pool we created for this TB
for sp in lxd_client.storage_pools.all():
    if TB_NAME in sp.name:
        print("Deleting storage pool {}".format(sp.name))
        sp.delete()

# Delete the network we created for this TB
for net in lxd_client.networks.all():
    if TB_NAME in net.name:
        print("Deleting network {}".format(net.name))
        net.delete(wait=True)

print("Done")
