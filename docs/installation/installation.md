# Installation guide

Ralph is distributed as Docker images published to Docker Hub:

  * [allegro/ralph](https://hub.docker.com/r/allegro/ralph) — the application image
  * [allegro/ralph-static-nginx](https://hub.docker.com/r/allegro/ralph-static-nginx) — static files served by Nginx

> **Note:** Debian/Ubuntu packages are no longer published. The packages
> already available on [packagecloud](https://packagecloud.io/allegro/ralph)
> remain installable but will not receive any updates. Please migrate to the
> Docker-based installation.

## Docker installation — recommended

Install [Docker](https://docs.docker.com/engine/install/) with the compose
plugin first.

### Create compose configuration

Use [docker/docker-compose.yml](https://github.com/allegro/ralph/blob/ng/docker/docker-compose.yml)
from the Ralph repository as a starting point and tweak it to your needs
(passwords, volumes, ports).

### Initialize the database

Run once, on the very first start:

    docker compose run --rm web init

This waits for the database, applies migrations, rebuilds the menu and
prompts for a superuser account.

### Run

    docker compose up -d

Ralph should now be accessible at ``http://127.0.0.1``.

### Upgrades

After pulling newer images, apply migrations with:

    docker compose run --rm web upgrade

### Configuration

The images read settings from environment variables (see the ``environment``
sections in the compose file), e.g. ``DATABASE_HOST``, ``DATABASE_USER``,
``DATABASE_PASSWORD``, ``REDIS_HOST``. They are translated to Django settings
inside the container. See the [configuration](./configuration.md) section for
the full reference.

### Troubleshooting

If something goes wrong, you can take a peek at these log files inside the
``web`` container:

    /var/log/ralph/ralph.log
    /var/log/ralph/gunicorn.error.log
    /var/log/ralph/gunicorn.access.log

### Next steps

For production usage it is a good idea to host the database outside of the
compose stack, use non-default credentials and terminate SSL on a load
balancer in front of Nginx.

Don't forget to read our quick start:
[https://ralph-ng.readthedocs.io/en/latest/user/quickstart/](https://ralph-ng.readthedocs.io/en/latest/user/quickstart/)!
