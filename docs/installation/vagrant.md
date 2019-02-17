### Preparation of Vagrant box

Create and enter a new parent directory for your Vagrant box:

    mkdir ralph_vagrant
    cd ralph_vagrant

Create Vagrant file in the parent directory:

    cat -> Vagrantfile
    Vagrant.configure("2") do |config|
      config.vm.box = "ubuntu/bionic64"
      config.vm.hostname = "ralph"
      config.vm.network "forwarded_port", guest: 80, host: 8000
      config.vm.provider "virtualbox" do |vb|
        vb.memory = "2048"
      end
    end
    ^D

Start and enter the box:

    vagrant up
    vagrant ssh
