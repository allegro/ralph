# Releasing Ralph

Ralph is released as Docker images (``allegro/ralph``,
``allegro/ralph-static-nginx`` and ``allegro/inkpy``) built from a multi-stage
Dockerfile (``docker/Dockerfile-prod``). Static assets are built with
node/gulp, Python dependencies are installed from ``uv.lock`` with
[uv](https://docs.astral.sh/uv/) — there are no intermediate packages
involved.

Versions are date-based tags (``YYYYMMDD.PATCH``) created from git —
see ``get_version.sh``.

## Releasing and publishing a new version

Properly releasing versions is one of the key duties of every Ralph
maintainer. It is necessary for Ralph maintainers to have their development
tools properly configured. For the details, see the
[Maintainer's development tools][3] section.

1. Switch to `ng` branch and ensure it is clean:
    ```
    git checkout ng
    git status
    ```
2. Pull the latest changes from the ng branch of the [upstream repository][1]:
    ```
    git pull upstream ng
    ```
3. Create and sign the release tag:
   ```
   mise run release-new-version
   ```
4. Enter your `gpg` key password, if asked, to sign the tag.
5. Verify the tag and its signature:
   ```
   git verify-tag <LATEST_TAG>
   ```
6. Push the tag to the upstream repository:
   ```
   git push upstream <LATEST_TAG>
   ```
7. Create a new GitHub release for the tag. This triggers the ``Publish``
   workflow which builds and pushes the Docker images.
8. Verify the workflow succeeded and the [Docker Hub repository][2] contains
   the new tag.

## Snapshot builds

Snapshot images (versioned ``<DATE>.<PATCH>-<BRANCH>-SNAPSHOT``) can be built
locally for testing:

```
mise run build-snapshot-docker-image
```

or built and published via the ``Publish snapshot`` GitHub workflow
(``workflow_dispatch``), which runs ``mise run publish-docker-snapshot-image``
for a selected branch.

[1]: https://github.com/allegro/ralph
[2]: https://hub.docker.com/r/allegro/ralph/tags
[3]: ./maintainers_devtools.md
