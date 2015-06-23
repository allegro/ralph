# Docker

Run Ralph using docker-compose (NOT FOR PRODUCTION USE RIGHT NOW!)

## Install
Install [docker-compose](http://docs.docker.com/compose/install/) first.


## Create compose configuration
Copy ``docker-compose.yml.tmpl`` outside ralph sources to docker-compose.yml
and tweak it.

## Build
Then build ralph::

    docker-compose build


To initialize database run::

    docker-compose run web /root/init.sh

Notice that this command should be executed only once, at the very beginning.

## Run
Run ralph at the end::

    docker-compose up

Ralph should be accessible at ``http://127.0.0.1`` (or if you are using ``boot2docker`` at ``$(boot2docker ip)``). Documentation is available at ``http://127.0.0.1/docs``.

If you are upgrading ralph image (source code) run::

    docker-compose run web /root/upgrade.sh
