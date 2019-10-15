# RPKI-Lab
This repository contains a tutorial that aims to allow you to effectively configure and play with an RPKI infrastructure. This tutorial has been given at the ITNOG "on the road" day hosted at Eolo on Sept. 27th, 2019 (eolo.it/nic).

The tutorial relies on four LXD containers and one Docker container. The topology, enforced by means of an underlying Open vSwitch bridge, is the following:
```
+--------------+                +--------------+                +------------+
|              | eth1      eth3 |              | eth2      eth0 |            |
|   RPKI+RTR   +----------------+      R0      +----------------+   ExaBGP   |
|              |                |              |                |            |
+---+----------+                +-----+--+-----+                +------------+
    | eth0                       eth0 |  | eth1
    |                                 |  |
    |                                 |  |
    |                  +------+       |  |       +------+
    |                  |      | eth0  |  |  eth1 |      |
    |                  |      +-------+  +-------+      |
    |                  |  R1  |                  |  R2  |
    |                  |      |                  |      |
    v                  |      | eth1        eth0 |      |
                       |      +------------------+      |
 docker0               +------+                  +------+

```
The containers contain the following software/packages:
- `Rn` are LXD containers running the FRRouting suite. BGP and OSPF (and zebra) are started automatically when the containers get created. For more details about FRRouting, please visit [https://frrouting.org/](https://frrouting.org/).
- `ExaBGP` runs the ExaBGP daemon. The daemon starts automatically when the containers gets created. See [## Standard configuration][Introduction] for more details about the standard configuration. Documentation about ExaBGP is available at [https://github.com/Exa-Networks/exabgp](https://github.com/Exa-Networks/exabgp).
- `RPKI-RTR` is a Docker container instantiated from the image available at [https://hub.docker.com/r/cloudflare/gortr](https://hub.docker.com/r/cloudflare/gortr). More details about this project are available at [https://rpki.cloudflare.com/](https://rpki.cloudflare.com/).  

## First step: Setup dependencies
Before you can start running this tutorial, you will need to install a few dependencies on your system. Required packages for this tutorial are:
 - Open vSwitch
 - Docker
 - LXD
 - Python3

A few python libraries are also needed:
 - pylxd
 - docker
 - netifaces

## Second step: Build the LXD images
The repository comes with two bash scripts: `create_image_exa.sh` and `create_image_frr.sh` that can be used to build the two LXD images:
```
root@ubuntu:~/rpki-lab$ ./create_image_frr.sh frr
[...]
root@ubuntu:~/rpki-lab$ ./create_image_exa.sh exa
[...]
root@ubuntu:~/rpki-lab$ ls -l frr*gz
-rw-r--r--  1 root root       220 Oct  9 11:30 frr_metadata.tar.gz
-rw-r--r--  1 root root 169939385 Oct  9 11:30 frr_rootfs.tar.gz
root@ubuntu:~/rpki-lab$ ls -l exa*gz
-rw-r--r--  1 root root       226 Oct  9 11:34 exa_metadata.tar.gz
-rw-r--r--  1 root root 355542208 Oct  9 11:34 exa_rootfs.tar.gz
```

## Third step: Instantiate the test-bed and work with containers
The script `create_tb.py` instantiates the test-bed. It requires a parameters which will be used as a prefix for the names of the containers, network, storage pool, etc.
```
root@ubuntu:~/rpki-lab$ ./create_tb.py test
Done with creating network test
Done with creating storage pool test
Done with creating profile test-frr
Done with creating profile test-exa
Done with creating image test-frr
Done with creating image test-exa
Container #0 started
Container #1 started
Container #2 started
Container for EXABGP started
Container for RPKI validator started
Setting up networking...Done
EXABGP started
==========================================================
 All done. Have fun!
==========================================================
```
At this point, given `test` the name of the test-bed, we have four LXD containers and one Docker container running on the machine:
```
root@ubuntu:~$ lxc list
+----------+---------+-------------------+------+------------+-----------+
|   NAME   |  STATE  |       IPV4        | IPV6 |    TYPE    | SNAPSHOTS |
+----------+---------+-------------------+------+------------+-----------+
| test-0   | RUNNING | 172.16.1.1 (eth2) |      | PERSISTENT | 0         |
|          |         | 10.1.1.14 (eth3)  |      |            |           |
+----------+---------+-------------------+------+------------+-----------+
| test-1   | RUNNING |                   |      | PERSISTENT | 0         |
+----------+---------+-------------------+------+------------+-----------+
| test-2   | RUNNING |                   |      | PERSISTENT | 0         |
+----------+---------+-------------------+------+------------+-----------+
| test-exa | RUNNING | 172.16.1.2 (eth0) |      | PERSISTENT | 0         |
+----------+---------+-------------------+------+------------+-----------+
```

```
root@ubuntu:~$ docker container list
CONTAINER ID        IMAGE                     COMMAND             CREATED             STATUS              PORTS                    NAMES
740a38ab3c3c        cloudflare/gortr:0.11.3   "./gortr"           2 hours ago         Up 2 hours          0.0.0.0:8282->8282/tcp   test-rpki
```

The following two sections offers a small cheat sheet of commands for the LXD containers, which are the ones that needs to be configured to run the tutorial. The Docker `test-rpki` container can be treated as a black-box tool, there is no need to run specific commands on that for what concerns this tutorial.

#### Working on the "router" containers
Containers running FRR come with the `vtysh` utility, that can be used for configuring the routing daemons. To open the "router" console of the n-th container you can use the command `lxc exec test-. vtysh`. Example:
```
root@ubuntu:~$ lxc exec test-0 vtysh

Hello, this is FRRouting (version 7.1).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

test-0#
```

#### Working with the "ExaBGP" container
ExaBGP starts inside a `screen`. Its configuration files are located inside the root directory of the container.
```
root@ubuntu:~$ lxc exec test-exa bash
root@test-exa:~# ls -l
total 8
-rw-r--r-- 1 root root 961 Sep 23 14:12 bgp.py
-rw-r--r-- 1 root root 241 Sep 23 14:12 exabgp.conf
root@test-exa:~# screen -ls
There is a screen on:
	106..test-exa	(10/09/19 14:57:35)	(Detached)
1 Socket in /run/screen/S-root.
```

## Standard configuration

A few IP addresses have been pre-configured to ease the tutorial:
- R0, eth2: 172.16.1.1/30
- R0, eth3: 10.1.1.14/30
- EXABGP, eth0: 172.16.1.2/30
- RPKI, eth1: 10.1.1.13/30

### Exabgp configuration
With the default `lxd/exa/exabgp.conf` file, the EXABGP daemon tries to establish a BGP session with 172.16.1.1 (which gets configured on R0 by default by our `create_tb.py` script), AS 35612. It will announce several routes, which have been configured on purpose to show the effectiveness of the RPKI facility. The routes that are advertised by EXABGP (all with next-hop 172.16.1.2) are:

| Network | AS path | Validity |
|--|--|--|
| 66.185.112.0/24 | 174, 2914, 42 | valid |
| 144.41.0.0/16 | 174, 553 | valid |
| 193.16.4.0/22 | 174, 1299, 680 | valid |
| 23.162.96.0/24 | 174 | invalid |
| 1.36.160.0/19 | 174 | invalid |
| 131.196.192.0/24 | 174, 16735, 16735, 28158, 1 | invalid |
| 194.20.8.0/21 | 8968, 3313 | unknown |
| 151.17.0.0/16 | 8968, 1267 | unknown |
| 211.13.0.0/17 | 1299, 2518, 2518 | valid |

## Credits
For further information about this tutorial, feel free to get in touch with us by sending an e-mail to rnd@eolo.it.
