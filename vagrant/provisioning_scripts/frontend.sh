#!/bin/bash

NODEJS_VERSION=${NODEJS_VERSION:-"6.9.2"}

cleanup_js() {
    rm -rf "$RALPH_DIR/node_moduled"
    rm -rf "$RALPH_DIR/bower_components"
}


install_node() {
    sudo npm install -g n
    sudo n "$NODEJS_VERSION"
}


install_js_packages() {
    pushd "$RALPH_DIR"
    npm install
    npm install gulp

    "$RALPH_DIR/node_modules/.bin/gulp"
    popd
}


provision_frontend() {
    echo "Starting configuration of Ralph's frontend."
    cleanup_js || true
    install_node
    install_js_packages
    echo "Configuration of Ralph's frontend succeeded."
}
