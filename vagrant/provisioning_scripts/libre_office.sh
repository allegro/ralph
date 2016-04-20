# Install LibreOffice for generating documents
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libreoffice-writer openjdk-7-jre unoconv \
    libreoffice-script-provider-python uno-libs3 \
    python3-uno

# copy libreoffice service's conf
sudo cp /home/vagrant/src/ralph/vagrant/upstart/soffice.conf /etc/init/soffice.conf

sudo start soffice
if [[ $? != 0 ]]; then
    sudo restart soffice
fi
