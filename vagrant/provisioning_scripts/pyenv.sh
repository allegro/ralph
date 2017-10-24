clean_up() {
    deactivate || true
    rm -rf $RALPH_VENV
}


setup_venv() {
    local activation_path="$RALPH_VENV/bin/activate"

    sudo pip3 install --upgrade pip
    sudo pip3 install virtualenv

    virtualenv -p $(which python3) "$RALPH_VENV"

    set +u
    source "$activation_path"
    set -u
}


install_ralph() {
    pushd "$RALPH_DIR"
    make install-dev
    popd
}


setup_user_env() {
    local settings_local_path="$RALPH_DIR/src/ralph/settings/local.py"
    local ralph_local_settings="from ralph.settings.dev import *  # noqa"
    printf -v ralph_dir_escaped  "%q" $"RALPH_DIR"

    cat "$RALPH_PROFILE_EXTENSIONS" > "$USER_PROFILE_PATH"

    sed -i "s~RALPH_DIR~$RALPH_DIR~g" "$USER_PROFILE_PATH"
    sed -i "s~RALPH_VENV~$RALPH_VENV~g" "$USER_PROFILE_PATH"

    source "$USER_PROFILE_PATH"

    # create local settings file
    if [ ! -f $settings_local_path ]; then
        echo "$ralph_local_settings" > $settings_local_path
    fi
}


provision_pyenv() {
    echo "Installing Ralph and its dependencies."
    clean_up || true
    setup_venv
    install_ralph
    setup_user_env
    echo "Installation of Ralph and its dependencies succeeded."
}
