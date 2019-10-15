#!/bin/bash

if [ $# -ne 1 ]
then
    echo "Usage: $0 <dir>"
    exit 1
fi

IMAGE_DIR=$1

# Clean-up
rm -rf ${IMAGE_DIR}

# Create folder
mkdir ${IMAGE_DIR}
debootstrap --arch=amd64 bionic ${IMAGE_DIR}
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot debootstrap" ; exit $rc ; fi

# Set-up apt repositories
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic main restricted\" > /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic main restricted\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic-updates main restricted\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic-updates main restricted\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic universe\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic universe\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic-updates universe\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic-updates universe\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic-updates multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic-updates multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://archive.ubuntu.com/ubuntu bionic-backports main restricted universe multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://archive.ubuntu.com/ubuntu bionic-backports main restricted universe multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://security.ubuntu.com/ubuntu bionic-security main restricted\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://security.ubuntu.com/ubuntu bionic-security main restricted\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://security.ubuntu.com/ubuntu bionic-security universe\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://security.ubuntu.com/ubuntu bionic-security universe\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb http://security.ubuntu.com/ubuntu bionic-security multiverse\" >> /etc/apt/sources.list"
chroot ${IMAGE_DIR} /bin/bash -c "echo \"deb-src http://security.ubuntu.com/ubuntu bionic-security multiverse\" >> /etc/apt/sources.list"

chroot ${IMAGE_DIR} /bin/bash -c "apt update && apt install -yq curl gnupg tcpdump ifupdown python3-pip vim screen"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot install packages" ; exit $rc ; fi

#######################################################
# EXABGP
#######################################################
echo "INSTALLING EXABGP"
chroot ${IMAGE_DIR} /bin/bash -c "pip3 install exabgp"
chroot ${IMAGE_DIR} /bin/bash -c "mkdir -p /usr/local/var/run/exabgp"
chroot ${IMAGE_DIR} /bin/bash -c "mkfifo /usr/local/var/run/exabgp/exabgp.{in,out}"
chroot ${IMAGE_DIR} /bin/bash -c "chmod 600 /usr/local/var/run/exabgp/exabgp.{in,out}"
chroot ${IMAGE_DIR} /bin/bash -c "mkdir -p /usr/local/etc/exabgp/"
chroot ${IMAGE_DIR} /bin/bash -c "exabgp --fi > /usr/local/etc/exabgp/exabgp.env"
chroot ${IMAGE_DIR} /bin/bash -c "sed -i 's/nobody/root/g' /usr/local/etc/exabgp/exabgp.env"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot install EXABGP" ; exit $rc ; fi

# Add config files
cp lxd/exa/exabgp.conf ${IMAGE_DIR}/root/exabgp.conf
cp lxd/exa/bgp.py ${IMAGE_DIR}/root/bgp.py

# Remove hostname
rm ${IMAGE_DIR}/etc/hostname
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot remove the hostname" ; exit $rc ; fi

#######################################################
# CREATE THE ROOTFS
#######################################################
echo "CREATE THE ROOTFS"
tar -cvzf exa_rootfs.tar.gz -C ${IMAGE_DIR} .
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot create the rootfs" ; exit $rc ; fi

#######################################################
# CREATE THE METADATA
#######################################################
echo "CREATE THE METADATA"
cat << EOF > metadata.yaml
architecture: "x86_64"
creation_date: $(date +%s)
properties:
architecture: "x86_64"
description: "EXABGP image"
os: "ubuntu"
release: "18.04"
EOF
tar -cvzf exa_metadata.tar.gz metadata.yaml
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot create the metadata" ; exit $rc ; fi

echo "DONE"

exit 0
