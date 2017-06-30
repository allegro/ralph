setup_ipxe() {
    local tftp_config_src="$RALPH_DIR/vagrant/conf/default-tftpd-hpa.conf"
    local tftp_config_dst="/etc/default/tftpd-hpa"
    local nginx_config_src="$RALPH_DIR/vagrant/conf/nginx.conf"
    local nginx_config_dst="/etc/nginx/sites-enabled/default"

    sudo mkdir -p "$RALPH_SRV_DIR"
    sudo mkdir -p "$RALPH_TFTP_DIR"

    sudo cp "$tftp_config_src" "$tftp_config_dst"
    sudo cp "$nginx_config_src" "$nginx_config_dst"

    sudo systemctl enable tftpd-hpa.service
    sudo systemctl restart tftpd-hpa.service
    sudo systemctl restart isc-dhcp-server.service
    sudo systemctl restart nginx.service
}


setup_dhcp_agent() {
    local dhcp_agent_src="$RALPH_DIR/contrib/dhcp_agent/dhcp_agent.py"
    local dhcp_agent_dst="$HOME_DIR/dhcp_agent.py"
    local crontab_file="$RALPH_DIR/vagrant/conf/crontab.txt"

    cp "$dhcp_agent_src" "$dhcp_agent_dst"
    chmod +x "$dhcp_agent_dst"

    sudo sed -i "s/RALPH_API_KEY/$RALPH_API_KEY/g" "$crontab_file"
    sudo crontab "$crontab_file"
}


setup_nat() {
    sudo sed -i "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g" /etc/sysctl.conf

    sudo iptables -A FORWARD -o eth0 -j ACCEPT
    sudo iptables -A FORWARD -i eth0 -j ACCEPT
    sudo iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE
}


provision_deployment() {
    echo "Starting configuration of deployment facilities."
    setup_ipxe
    setup_dhcp_agent
    setup_nat
    echo "Configuration of deployment facilities succeeded."
}
