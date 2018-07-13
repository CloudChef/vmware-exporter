#!/usr/bin/env bash
## download dependency rpms into ../packages/rpms ##
## download wheels into ../packages/wheels ##

CURDIR=$(dirname $0)
CONFIGDIR=$CURDIR/../configs
PACKAGESDIR=$CURDIR/../packages
RPMSDIR=$PACKAGESDIR/rpms
WHEELSDIR=$PACKAGESDIR/wheels
REQUIREMENTS=$CURDIR/../requirements.txt
LOGPATH=/var/log/cloudchef/vmware_exporter
EXECPATH=/opt/cloudchef/vmware-exporter

function pre_install()
{
    # install dependency rpms
    yum install -y $RPMSDIR/*.rpm
    # install required python packages
    pip install -r $REQUIREMENTS --no-index --find-links=$WHEELSDIR
    # create exec dir
    mkdir -p $EXECPATH
    # create log dir
    mkdir -p $LOGPATH
}

function install()
{
    cp -r $CURDIR/../vmware_exporter $EXECPATH
}

function post_install()
{
    # copy environment file
    cp $CONFIGDIR/cloudchef-vmware-exporter /etc/sysconfig/
    # copy systemd unit file
    cp $CONFIGDIR/cloudchef-vmware-exporter.service /usr/lib/systemd/system
    # Enable vmware-exporter service
    systemctl enable cloudchef-vmware-exporter.service
    # Start vmware-exporter service
    systemctl start cloudchef-vmware-exporter.service
}

pre_install
install
post_install
