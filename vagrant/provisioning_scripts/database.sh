cleanup_database() {
    echo "DROP DATABASE IF EXISTS $RALPH_DB_NAME" | sudo mysql -u root
}

setup_mysql_server() {
    local mysql_config_file="$MYSQL_CONF_D/ralph.cnf"
    local mysql_config_source="$RALPH_DIR/vagrant/conf/ralph_mysql.conf"

    sudo cp "$mysql_config_source" "$mysql_config_file"
    sudo systemctl restart mysql.service
}


create_database() {
    echo "CREATE DATABASE $RALPH_DB_NAME DEFAULT CHARACTER SET 'utf8'" | sudo mysql -u root
    echo "GRANT ALL ON $RALPH_DB_NAME.* TO $RALPH_DB_USER_NAME@'%' IDENTIFIED BY '$RALPH_DB_USER_PASS'; FLUSH PRIVILEGES" | sudo mysql -u root
}


setup_ralph_database() {
    dev_ralph migrate
    dev_ralph createsuperuser --noinput --username "$RALPH_SUPERUSER_NAME" --email "$RALPH_SUPERUSER_NAME@example.net"

    RALPH_SUPERUSER_NAME="$RALPH_SUPERUSER_NAME" \
        RALPH_SUPERUSER_PASSWORD="$RALPH_SUPERUSER_PASSWORD" \
        python "$RALPH_DIR/vagrant/provisioning_scripts/createsuperuser.py"

    pushd "$RALPH_DIR"
    make menu
    popd
}


provision_database() {
    echo "Starting configuration of the database."
    cleanup_database || true
    setup_mysql_server
    create_database
    setup_ralph_database
    echo "Configuration of the database succeeded."
}
