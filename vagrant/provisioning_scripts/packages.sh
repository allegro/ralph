__RALPH_REQUIRED_PACKAGES_DEFAULT="\
    build-essential \
    git \
    htop \
    iptables-persistent \
    isc-dhcp-server \
    libffi-dev \
    libldap2-dev \
    libmysqlclient-dev \
    libmysqld-dev \
    libreoffice-script-provider-python \
    libreoffice-writer \
    libsasl2-dev \
    libsass-dev \
    libssl-dev \
    make \
    mysql-server \
    nginx \
    nodejs \
    npm \
    openjdk-8-jre unoconv \
    python3 \
    python3-dev \
    python3-pip \
    python3-uno \
    python3-venv \
    redis-server \
    tftpd-hpa \
    uno-libs3 \
"
RALPH_REQUIRED_PACKAGES=${RALPH_REQUIRED_PACKAGES:-"$__RALPH_REQUIRED_PACKAGES_DEFAULT"}


provision_packages() {
    echo "Installing system packages."
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $RALPH_REQUIRED_PACKAGES
    echo "Installation of system packages succeeded."
}

