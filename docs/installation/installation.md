# Installation guide

For production, we provide both deb package and docker(compose) image.
We only support Ubuntu 14.04 Trusty distribution on the AMD64 platform.

On the other hand, if you are developer, we strongly suggest using our `Vagrant` inside the `vagrant` directory
with many development *bells and whistles* included.

## Debian/Ubuntu package - recommended

Make sure, your installation is clean Ubuntu 14.04, without any other packages installed,
and `apt-transport-https` installed.

    sudo apt-get update && sudo apt-get install apt-transport-https

Now, add our official ralph repository:

    sudo apt-key adv --keyserver  hkp://keyserver.ubuntu.com:80 --recv-keys 379CE192D401AB61
    sudo sh -c "echo 'deb https://dl.bintray.com/vi4m/ralph wheezy main' >  /etc/apt/sources.list.d/vi4m_ralph.list"

Then, just install ralph the traditional way:

    sudo apt-get update
    sudo apt-get install ralph-core redis-server mysql-server

Note: Main www instance of Ralph requires redis and mysql server installed. If you want to install only ralph agent somewhere, just install `ralph-core` and point it to the particular mysql and redis instance somewhere on your network.


### Configuration


Create the database.

    > mysql -u root
    > CREATE database ralph default character set 'utf8';

### Settings

We are working on some sane configuration management files.
Currently, we just read some environment variables, so just paste somewhere in your ~/.profile following environment variables customizing it to your needs.


cat ~/.profile

    export DATABASE_NAME=ralph
    export DATABASE_USER=someuser
    export DATABASE_PASSWORD=somepassword
    export DATABASE_HOST=127.0.0.1
    export PATH=/opt/ralph/ralph-core/bin/:$PATH
    export RALPH_DEBUG=1

### Initialization
1. Type `ralph migrate` to create tables in your database.
2. Type `ralph sitetree_resync_apps` to reload menu.
3. Type `ralph createsuperuser` to add new user.

Run your ralph instance with `ralph runserver 0.0.0.0:8000`

Now, point your browser to the http://localhost:8000 and log in. Happy Ralphing!

## Docker installation (experimental)

You can find experimental docker-compose configuration in [https://github.com/allegro/ralph/tree/ng/contrib](https://github.com/allegro/ralph/tree/ng/contrib) directory.
Be aware, it is still a beta.

### Install

Install docker and [docker-compose](http://docs.docker.com/compose/install/) first.


### Create compose configuration

Copy ``docker-compose.yml.tmpl`` outside ralph sources to docker-compose.yml
and tweak it.

### Build

Then build ralph:

    docker-compose build


To initialize database run:

    docker-compose run --rm web /root/init.sh

Notice that this command should be executed only once, at the very beginning.

If you need to populate Ralph with some demonstration data run:

    docker-compose run --rm web ralph demodata

### Run

Run ralph at the end:

    docker-compose up -d

Ralph should be accessible at ``http://127.0.0.1`` (or if you are using ``boot2docker`` at ``$(boot2docker ip)``). Documentation is available at ``http://127.0.0.1/docs``.

If you are upgrading ralph image (source code) run:

    docker-compose run --rm web /root/upgrade.sh


# Migration from Ralph 2

If you used Ralph 2 before and want to save all your data see [Migration from Ralph 2 guide](./data_migration.md#migration_ralph2)
