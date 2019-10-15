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

chroot ${IMAGE_DIR} /bin/bash -c "apt update && apt install -yq curl gnupg tcpdump ifupdown"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot install curl" ; exit $rc ; fi

#######################################################
# FRR (taken from https://deb.frrouting.org)
#######################################################
echo "INSTALLING FRR"
chroot ${IMAGE_DIR} /bin/bash -c "curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add -"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute FRR command #1" ; exit $rc ; fi
# possible values for FRRVER: frr-6 frr-7 frr-stable
chroot ${IMAGE_DIR} /bin/bash -c "echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) frr-stable | tee -a /etc/apt/sources.list.d/frr.list"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute FRR command #2" ; exit $rc ; fi
chroot ${IMAGE_DIR} /bin/bash -c "apt update && apt install -yq frr frr-rpki-rtrlib librtr-dev librtr0 rtr-tools frr-pythontools"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute FRR command #3" ; exit $rc ; fi

#######################################################
# CONFIGURE THE ROOTFS
#######################################################
echo "CONFIGURE THE ROOTFS"
# Add library path
chroot ${IMAGE_DIR} /bin/bash -c "echo \"include /etc/ld.so.conf.d/*.conf\" > /etc/ld.so.conf"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #4" ; exit $rc ; fi
chroot ${IMAGE_DIR} /bin/bash -c "echo \"include /usr/local/lib\" >> /etc/ld.so.conf"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #5" ; exit $rc ; fi

# Configure sysctl FRR
cp lxd/frr/zebra.service ${IMAGE_DIR}/lib/systemd/system/
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #6" ; exit $rc ; fi
cp lxd/frr/bgpd.service ${IMAGE_DIR}/lib/systemd/system/
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #7" ; exit $rc ; fi
cp lxd/frr/ospfd.service ${IMAGE_DIR}/lib/systemd/system/
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #8" ; exit $rc ; fi

# Required configuration files
mkdir -p ${IMAGE_DIR}/etc/frr/
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #9" ; exit $rc ; fi
touch ${IMAGE_DIR}/etc/frr/zebra.conf
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #10" ; exit $rc ; fi
touch ${IMAGE_DIR}/etc/frr/bgpd.conf
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #11" ; exit $rc ; fi
touch ${IMAGE_DIR}/etc/frr/ospf.conf
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #12" ; exit $rc ; fi
mkdir -p ${IMAGE_DIR}/usr/local/etc
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #13" ; exit $rc ; fi
touch ${IMAGE_DIR}/usr/local/etc/vtysh.conf
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #14" ; exit $rc ; fi

# Start FRR at boot
chroot ${IMAGE_DIR} /bin/bash -c "/bin/systemctl enable zebra.service"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #15" ; exit $rc ; fi
chroot ${IMAGE_DIR} /bin/bash -c "/bin/systemctl enable bgpd.service"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #16" ; exit $rc ; fi
chroot ${IMAGE_DIR} /bin/bash -c "/bin/systemctl enable ospfd.service"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #17" ; exit $rc ; fi

# Remove hostname
rm ${IMAGE_DIR}/etc/hostname
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #18" ; exit $rc ; fi
/bin/bash -c "echo \"ldconfig\" >> ${IMAGE_DIR}/root/.bashrc"
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot execute command #19" ; exit $rc ; fi

#######################################################
# CREATE THE ROOTFS
#######################################################
echo "CREATE THE ROOTFS"
tar -cvzf frr_rootfs.tar.gz -C ${IMAGE_DIR} .
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
description: "FRR image"
os: "ubuntu"
release: "18.04"
EOF
tar -cvzf frr_metadata.tar.gz metadata.yaml
rc=$?; if [ $rc -ne 0 ]; then echo "Cannot create the metadata" ; exit $rc ; fi

echo "DONE"

exit 0
