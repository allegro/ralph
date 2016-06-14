#!/bin/bash
set -e

RALPH_API_KEY='api_key'

sudo apt-get update -y

sudo apt-get install -y tftpd-hpa
sudo apt-get install -y htop
sudo apt-get install -y iptables-persistent

sudo update-rc.d tftpd-hpa defaults
sudo mkdir /srv/www

sudo cp /vagrant/conf/dhcpd.conf /etc/dhcp/dhcpd.conf
sudo cp /vagrant/conf/default-tftpd-hpa.conf /etc/default/tftpd-hpa
sudo cp /vagrant/conf/nginx.conf /etc/nginx/sites-enabled/default

cd ~ && wget https://raw.githubusercontent.com/allegro/ralph/ng/contrib/dhcp_agent/dhcp_agent.py
chmod +x dhcp_agent.py
sudo sed -i "s/RALPH_API_KEY/$RALPH_API_KEY/g" /vagrant/conf/crontab.txt
sudo crontab /vagrant/conf/crontab.txt

sudo service isc-dhcp-server restart
if [[ $? != 0 ]]; then
    sudo service isc-dhcp-server start
fi

sudo sed -i "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g" /etc/sysctl.conf

sudo iptables -A FORWARD -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -j ACCEPT
sudo iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE
