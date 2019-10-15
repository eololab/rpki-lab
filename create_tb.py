#!/usr/bin/env python3
 
import sys
import pylxd
import random
import string
import urllib
import subprocess
import re
import os
import netifaces
import docker

if len(sys.argv) != 2:
    print("Usage:",sys.argv[0],"<test-bed name>")
    sys.exit(1)

if os.geteuid() != 0:
    print("You need root permissions to set-up your test-bed")
    sys.exit(1)

# Name of the test-bed
TB_NAME = sys.argv[1]
 
# Number of containers
NUM_OF_CONTAINERS = 3

# Create a lxd_client and a docker_client
lxd_client = pylxd.Client()
docker_client = docker.from_env()
 
# Procedure for adding flow into ovs bridge
def addFlow(bridge, in_port, out_port, bidirectional=True):
    out = subprocess.run(['ovs-ofctl', 'add-flow', str(bridge), 'priority=10,in_port='+str(in_port)+',actions=output:'+out_port])
    if bidirectional:
        out = subprocess.run(['ovs-ofctl', 'add-flow', str(bridge), 'priority=10,in_port='+str(out_port)+',actions=output:'+in_port])

######################################################################
# NETWORK
######################################################################
# Create a new OVS bridge for this tb
try:
    lxd_client.networks.get(TB_NAME)
    print("Network {} already exists. Exiting...".format(TB_NAME))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass
network = lxd_client.networks.create(TB_NAME, description='FRR tb network', type='bridge', config={'bridge.driver': 'openvswitch'})
# Delete flows from the bridge - they will be added later
out = subprocess.run(['ovs-ofctl', 'del-flows', TB_NAME])
out = subprocess.run(['ovs-ofctl', 'add-flow', TB_NAME, 'priority=0,actions=drop'])
print("Done with creating network {}".format(TB_NAME))
 
######################################################################
# STORAGE POOL
######################################################################
# Create a storage pool for this tb
try:
    lxd_client.storage_pools.get(TB_NAME)
    print("Storage pool {} already exists. Exiting...".format(TB_NAME))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass
storage_pool = lxd_client.storage_pools.create({"config": {"size": "15GB"}, "driver": "btrfs", "name": TB_NAME})
print("Done with creating storage pool {}".format(TB_NAME))

######################################################################
# CREATE PROFILES
######################################################################
# Create a profile with five interfaces for the switches
try:
    lxd_client.profiles.get(TB_NAME+"-frr")
    print("Profile {} already exists. Exiting....".format(TB_NAME+"-frr"))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass
profile = lxd_client.profiles.create(TB_NAME+"-frr",
        devices={
	    'root': {'path': '/', 'pool': TB_NAME, 'type': 'disk'},
            'eth0': {'name': 'eth0', 'nictype': 'bridged', 'parent': TB_NAME, 'type': 'nic'},
            'eth1': {'name': 'eth1', 'nictype': 'bridged', 'parent': TB_NAME, 'type': 'nic'},
            'eth2': {'name': 'eth2', 'nictype': 'bridged', 'parent': TB_NAME, 'type': 'nic'},
            'eth3': {'name': 'eth3', 'nictype': 'bridged', 'parent': TB_NAME, 'type': 'nic'},
            'eth4': {'name': 'eth4', 'nictype': 'bridged', 'parent': TB_NAME, 'type': 'nic'},
        })
print("Done with creating profile {}".format(TB_NAME+"-frr"))

# Create a profile with one interface for EXA
try:
    lxd_client.profiles.get(TB_NAME+"-exa")
    print("Profile {} already exists. Exiting....".format(TB_NAME+"-exa"))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass
profile = lxd_client.profiles.create(TB_NAME+"-exa",
        devices={
	    'root': {'path': '/', 'pool': TB_NAME, 'type': 'disk'},
            'eth0': {'name': 'eth0', 'nictype': 'bridged', 'parent': TB_NAME, 'type': 'nic'},
        })
print("Done with creating profile {}".format(TB_NAME+"-exa")) 

######################################################################
# CREATE IMAGES
######################################################################
# Create an image from the FRR rootfs and metadata
try:
    lxd_client.images.get_by_alias(TB_NAME+"-frr")
    print("Image {} already exists. Exiting...".format(TB_NAME+"-frr"))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass
with open('frr_rootfs.tar.gz', 'rb') as f:
    image_data = f.read()
with open('frr_metadata.tar.gz', 'rb') as f:
    metadata = f.read()
try:
    image = lxd_client.images.create(image_data, metadata=metadata, public=False, wait=True)
    image.add_alias(TB_NAME+"-frr", "FRR image")
except pylxd.exceptions.LXDAPIException as e:
    print(e)
    sys.exit(1)
print("Done with creating image {}".format(TB_NAME+"-frr"))
 
# Create an image from the EXA rootfs and metadata
try:
    lxd_client.images.get_by_alias(TB_NAME+"-exa")
    print("Image {} already exists. Exiting...".format(TB_NAME+"-exa"))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass
with open('exa_rootfs.tar.gz', 'rb') as f:
    image_data = f.read()
with open('exa_metadata.tar.gz', 'rb') as f:
    metadata = f.read()
try:
    image = lxd_client.images.create(image_data, metadata=metadata, public=False, wait=True)
    image.add_alias(TB_NAME+"-exa", "EXABGP image")
except pylxd.exceptions.LXDAPIException as e:
    print(e)
    sys.exit(1)
print("Done with creating image {}".format(TB_NAME+"-exa"))

######################################################################
# CREATE CONTAINERS
######################################################################
# Istantiate the LXD FRR containers
for c_id in range(NUM_OF_CONTAINERS):
    container_name = TB_NAME+'-'+str(c_id)
    try:
        lxd_client.containers.get(container_name)
        print("Container {} already exists. Exiting...".format(container_name))
        sys.exit(1)
    except pylxd.exceptions.NotFound as e:
        pass

    config = {'name': container_name, 'source': {'type': 'image', 'alias': TB_NAME+'-frr'}, 'profiles': ['default', TB_NAME+'-frr'] }
    cont = lxd_client.containers.create(config, wait=True)
    cont.start(wait=True)
    # Create a loBGP loopback
    cont.execute("ip link add loBGP type dummy".split())
    cont.execute("ip link set loBGP up".split())
    print("Container #"+str(c_id)+" started")

# Istantiate the EXA container
container_name = TB_NAME+'-exa'
try:
    lxd_client.containers.get(container_name)
    print("Container {} already exists. Exiting...".format(container_name))
    sys.exit(1)
except pylxd.exceptions.NotFound as e:
    pass

config = {'name': container_name, 'source': {'type': 'image', 'alias': TB_NAME+'-exa'}, 'profiles': ['default', TB_NAME+'-exa'] }
cont = lxd_client.containers.create(config, wait=True)
cont.start(wait=True)
print("Container for EXABGP started")

# Istantiate the RPKI validator container
container_name = TB_NAME+'-rpki'
try:
    docker_client.containers.get(container_name)
    print("Container {} already exists. Exiting...".format(container_name))
    sys.exit(1)
except docker.errors.NotFound as e:
    pass
container = docker_client.containers.run('cloudflare/gortr:0.11.3', name=container_name, remove=True, detach=True, privileged=True, ports={'8282/tcp': 8282})

# Connect the docker rpki to the ovs bridge
subprocess.run(['ovs-docker', 'add-port', TB_NAME, 'eth1', TB_NAME+"-rpki", '--ipaddress=10.1.1.13/30'])

print("Container for RPKI validator started")


######################################################################
# NETWORKING
######################################################################
print("Setting up networking...", end="")
# Set-up networking
host_ifaces = {}
for iface in netifaces.interfaces():
    # Read ifindex and iflink
    with open('/sys/class/net/'+iface+'/ifindex', 'r') as f:
        ifindex = int(f.read().strip())
    with open('/sys/class/net/'+iface+'/iflink', 'r') as f:
        iflink = int(f.read().strip())
    host_ifaces[ifindex] = {'name': iface, 'peer_id': iflink}

# Get ifaces from the containers
ifaces = {}
ifaces_map = {}
try:
    for container_name in [TB_NAME+'-'+str(suffix) for suffix in ['exa']+[i for i in range(NUM_OF_CONTAINERS)]]:
        cont = lxd_client.containers.get(container_name)
        cont_profiles = [lxd_client.profiles.get(p) for p in cont.profiles]
        nics = set([k for p in cont_profiles for k in p.devices if p.devices[k]['type'] == 'nic'])
 
        cont_ifaces = {}
        # Read ifindex and iflink
        for iface in nics:
            ifindex = int(cont.execute(['cat', '/sys/class/net/'+iface+'/ifindex']).stdout.strip())
            iflink = int(cont.execute(['cat', '/sys/class/net/'+iface+'/iflink']).stdout.strip())
            cont_ifaces[ifindex] = {'name': iface, 'peer_id': iflink}
        ifaces[container_name] = cont_ifaces
        ifaces_map[container_name] = {}
    # docker container has only one interface to map: eth1
    container_name = TB_NAME+"-rpki"
    cont = docker_client.containers.get(container_name)
    cont_ifaces = {}
    ifindex = int(cont.exec_run(['cat', '/sys/class/net/eth1/ifindex']).output.strip())
    iflink = int(cont.exec_run(['cat', '/sys/class/net/eth1/iflink']).output.strip())
    cont_ifaces[ifindex] = {'name': 'eth1', 'peer_id': iflink}
    ifaces[container_name] = cont_ifaces
    ifaces_map[container_name] = {}

except Exception as e:
    print(e)
    sys.exit(1)

# Create the mapping
for container_name in [TB_NAME+'-'+str(suffix) for suffix in ['exa']+[i for i in range(NUM_OF_CONTAINERS)]]:
    cont_ifaces = ifaces[container_name]
    for iface in cont_ifaces:
        iface_name = cont_ifaces[iface]['name']
        peer_id = cont_ifaces[iface]['peer_id']
        ifaces_map[container_name][iface_name] = host_ifaces[peer_id]['name']
# docker
container_name = TB_NAME+'-rpki'
cont_ifaces = ifaces[container_name]
for iface in cont_ifaces:
    iface_name = cont_ifaces[iface]['name']
    peer_id = cont_ifaces[iface]['peer_id']
    ifaces_map[container_name][iface_name] = host_ifaces[peer_id]['name']

# Connect ifaces by means of ovs flows
addFlow(TB_NAME, ifaces_map[TB_NAME+'-0']['eth0'], ifaces_map[TB_NAME+'-1']['eth0'])
addFlow(TB_NAME, ifaces_map[TB_NAME+'-1']['eth1'], ifaces_map[TB_NAME+'-2']['eth0'])
addFlow(TB_NAME, ifaces_map[TB_NAME+'-0']['eth1'], ifaces_map[TB_NAME+'-2']['eth1'])
                           
addFlow(TB_NAME, ifaces_map[TB_NAME+'-0']['eth2'], ifaces_map[TB_NAME+'-exa']['eth0'])

addFlow(TB_NAME, ifaces_map[TB_NAME+'-rpki']['eth1'], ifaces_map[TB_NAME+'-0']['eth3'])

print("Done")


print("Pre-configuring IP addresses...", end="")
# Pre-configure IP addresses for all interfaces
container_name = TB_NAME+'-0'
try:
    container = lxd_client.containers.get(container_name)
except pylxd.exceptions.NotFound as e:
    print("Container {} does not exist. Exiting...".format(container_name))
    sys.exit(1)
container.execute(['/usr/bin/vtysh', '-c', 'configure terminal', '-c', 'interface eth2', '-c', 'description "To EXA"', '-c', 'ip address 172.16.1.1/30'])
container.execute(['/usr/bin/vtysh', '-c', 'configure terminal', '-c', 'interface eth3', '-c', 'description "To RPKI validator"', '-c', 'ip address 10.1.1.14/30'])
container.execute(['/usr/bin/vtysh', '-c', 'write'])

container_name = TB_NAME+'-exa'
try:
    container = lxd_client.containers.get(container_name)
except pylxd.exceptions.NotFound as e:
    print("Container {} does not exist. Exiting...".format(container_name))
    sys.exit(1)
container.execute(['ip', 'addr', 'add', '172.16.1.2/30', 'dev', 'eth0'])
print("Done")

# Start EXABGP in background
try:
    container = lxd_client.containers.get(TB_NAME+'-exa')
    out = container.execute(['/usr/bin/screen', '-d', '-m', '/usr/local/bin/exabgp', '/root/exabgp.conf'])
except pylxd.exceptions.NotFound as e:
    print("Container {} does not exist. Exiting...".format(container_name))
    sys.exit(1)
print("EXABGP started")

print("==========================================================")
print(" All done. Have fun!")
print("==========================================================")

# exit
sys.exit(0)
