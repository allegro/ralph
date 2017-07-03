#!/bin/bash
set -eu

# Common use settings
VM_USER=${VM_USER:-ubuntu}
HOME_DIR="/home/$VM_USER"
RALPH_DIR=${RALPH_DIR:-"$HOME_DIR/ralph"}
RALPH_VENV=${RALPH_VENV:-"$HOME_DIR/venv"}
RALPH_PROFILE_EXTENSIONS=${RALPH_PROFILE_EXTENSIONS:-"$RALPH_DIR/vagrant/provisioning_scripts/profile_extensions"}
USER_PROFILE_PATH=${USER_PROFILE_PATH:-"$HOME_DIR/.profile"}

# Deployment variables
RALPH_API_KEY=${RALPH_API_KEY:-"api_key"}
RALPH_SRV_DIR=${RALPH_SRV_DIR:-"/srv/www"}
RALPH_TFTP_DIR=${RALPH_TFTP_DIR:-"/opt/tftp"}

# Database settings
RALPH_DB_NAME=${RALPH_DB_NAME:-"ralph_ng"}
RALPH_DB_USER_NAME=${RALPH_DB_USER_NAME:-"ralph_ng"}
RALPH_DB_USER_PASS=${RALPH_DB_USER_PASS:-"ralph_ng"}
MYSQL_CONF_D=${MYSQL_CONF_D:-"/etc/mysql/conf.d/"}

# System settings
SYSTEMD_SERVICES_DIR=${SYSTEMD_SERVICES_DIR:-"/etc/systemd/system"}

# Networking settings
RALPH_DHCP_INTERFACE=${RALPH_DHCP_INTERFACE:-"eth1"}


for f in $(ls $RALPH_DIR/vagrant/provisioning_scripts/*.sh); do
    source "$f"
done


provision_packages
provision_pyenv
provision_database
provision_frontend
provision_soffice
provision_dhcp
provision_deployment
