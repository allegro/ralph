cleanup_dhcp(){
    sudo systemctl stop isc-dhcp-server.service || true
}


setup_dhcp() {
    local ip_addr=`/sbin/ifconfig $RALPH_DHCP_INTERFACE | grep "inet addr" | awk -F: '{print $2}' | awk '{print $1}'`
    local dhcp_conf_src="$RALPH_DIR/vagrant/conf/dhcpd.conf"
    local dhcp_conf_dst="/etc/dhcp/dhcpd.conf"
    local ipxe_conf_src="$RALPH_DIR/vagrant/conf/ipxe.options"
    local ipxe_conf_dst="/etc/dhcp/ipxe.options"
    local isc_server_config="/etc/default/isc-dhcp-server"

    sudo cp "$dhcp_conf_src" "$dhcp_conf_dst"
    sudo cp "$ipxe_conf_src" "$ipxe_conf_dst"

    sudo sed -i "s/RALPH_HOST/$ip_addr/g" $dhcp_conf_dst
    sudo sed -i "s/INTERFACES=\"\"/INTERFACES=\"$RALPH_DHCP_INTERFACE\"/g" "$isc_server_config"

    sudo systemctl start isc-dhcp-server.service
}


provision_dhcp() {
    echo "Starting configuration of the DHCP daemon."
    cleanup_dhcp || true
    setup_dhcp
    echo "Configuration of the DHCP daemon succeeded."
}
