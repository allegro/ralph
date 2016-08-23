#!/bin/bash

sudo apt-get install -y isc-dhcp-server

ETH='eth1'
IP=`/sbin/ifconfig $ETH | grep "inet addr" | awk -F: '{print $2}' | awk '{print $1}'`
sudo cp /vagrant/conf/dhcpd.conf /etc/dhcp/dhcpd.conf
sudo cp /vagrant/conf/ipxe.options /etc/dhcp/ipxe.options
sudo sed -i "s/RALPH_HOST/$IP/g" /etc/dhcp/dhcpd.conf
sudo sed -i "s/INTERFACES=\"\"/INTERFACES=\"$ETH\"/g" /etc/default/isc-dhcp-server


sudo start isc-dhcp-server
if [[ $? != 0 ]]; then
    sudo restart isc-dhcp-server
fi
