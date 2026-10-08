# Ralph

## Update - 2025/02

As Allegro, we continue to publish Ralph's source code and will maintain its development under a "Sources only" model, without guarantees. We believe this approach will be beneficial, allowing everyone to use and build upon the software. Our current goal is to modernize the software and ensure its long-term maintainability, and we're investing into it in 2025.

However, we are not operating under a contribution-based model. While we welcome discussions, we do not guarantee responses to issues or support for pull requests. If you require commercial support, please visit http://ralph.discourse.group.

We sincerely appreciate all past contributions that have shaped Ralph into the powerful tool it is today, and encourage the community to continue using it.


## Overview

Ralph is full-featured Asset Management, DCIM and CMDB system for data centers and back offices.

Features:

* keep track of assets purchases and their life cycle
* flexible flow system for assets life cycle
* data center and back office support
* dc visualization built-in

It is an Open Source project provided on Apache v2.0 License.

[![Gitter](https://img.shields.io/gitter/room/gitterHQ/gitter.svg)](https://gitter.im/allegro/ralph?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://github.com/allegro/ralph/actions/workflows/main.yml/badge.svg)](https://github.com/allegro/ralph/actions/workflows/main.yml)
[![Coverage Status](https://coveralls.io/repos/allegro/ralph/badge.svg?branch=ng&service=github)](https://coveralls.io/github/allegro/ralph?branch=ng)

## Live demo:

http://ralph-demo.allegro.tech/

* login: ralph
* password: ralph

If the demo is down, you can create your own in under a minute with:
```
alias docker="sudo docker"
DB=$(docker run --rm --env MARIADB_USER=ralph --env MARIADB_PASSWORD=ralph --env MARIADB_DATABASE=ralph_ng --env MARIADB_ROOT_PASSWORD=ralph -d mariadb)
sleep 10
RALPH=$(docker run --rm --env DATABASE_NAME=ralph_ng --env DATABASE_USER=ralph --env DATABASE_PASSWORD=ralph --env DATABASE_HOST=$DB --env RALPH_DEBUG=1 --link $DB -d allegro/ralph)
docker exec -ti $RALPH ralph migrate # wait for this to finish 
cat <<--- > ralph.conf
server {

    listen 80;
    client_max_body_size 512M;

    proxy_set_header Connection "";
    proxy_http_version 1.1;
    proxy_connect_timeout  300;
    proxy_read_timeout 300;

    access_log /var/log/nginx/ralph-access.log;
    error_log /var/log/nginx/ralph-error.log;

    location /static {
        alias /static;
        access_log        off;
        log_not_found     off;
        expires 1M;
    }

    #location /media {
    #    alias /var/local/ralph/media;
    #    add_header Content-disposition "attachment";
    #}

    location / {
        proxy_pass http://$RALPH:8000;
        include /etc/nginx/uwsgi_params;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
---
NGINX=$(docker run --rm -v `pwd`/ralph.conf:/etc/nginx/conf.d/default.conf:ro --link $RALPH -p 7777:80 -d nginx)
sleep 3
docker cp $RALPH:/usr/share/ralph/static - | docker cp - $NGINX:/
docker exec -ti $RALPH ralph createsuperuser # creates a login user and password
```
And then navigating to http://localhost:7777
If it fails, increase the sleep values or run the docker commands in separate terminals with -ti instead of -d. so you can know when the image is ready for the next one. 

Clean up with `docker stop $NGINX $RALPH $MARIADB; # and remove the downloaded images docker rmi nginx allegro/ralph mariadb`

## Screenshots

![img](https://github.com/allegro/ralph/blob/ng/docs/img/welcome-screen-1.png?raw=true)

![img](https://github.com/allegro/ralph/blob/ng/docs/img/welcome-screen-2.png?raw=true)

![img](https://github.com/allegro/ralph/blob/ng/docs/img/welcome-screen-3.png?raw=true)


## Documentation
Visit our documentation on [readthedocs.org](https://ralph-ng.readthedocs.org)

## Getting help

* Online forum for Ralph community: https://ralph.discourse.group
