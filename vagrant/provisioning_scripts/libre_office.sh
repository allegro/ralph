install_soffice_service() {
    local systemd_config_source="$RALPH_DIR/vagrant/systemd/soffice.service"
    local systemd_config_dst="$SYSTEMD_SERVICES_DIR/soffice.service"

    sudo cp $systemd_config_source $SYSTEMD_SERVICES_DIR
    sudo chmod 0664 $systemd_config_dst

    sudo systemctl daemon-reload
    sudo systemctl start soffice.service
    sudo systemctl enable soffice.service
}


provision_soffice() {
    echo "Starting configuration of Libre Office daemon."
    install_soffice_service
    echo "Configuration of Libre Office daemon succeeded."
}
