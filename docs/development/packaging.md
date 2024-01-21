# Deb package for Ubuntu

The way Ralph is made makes changing versions of its dependencies challenging;
consequently, in order to provide a deb package for [Ubuntu] it is necessary to
use  `dh_virtualenv` which installs all dependencies into a virtualenv and packs
the latter into a package. Although this approach is not blessed by either
[Debian] or Ubuntu maintainers, it provides a healthy compromise between the
availability of the Ralph package and the effort required to make one.

The package is built and published to [packagecloud] by the Ralph core maintainers.
This document describes what is necessary to know and to have for a maintainer
to be able to build, test and publish the package.

## Releasing and publishing new versions

Properly releasing versions is one of the key duties of every Ralph maintainer.
Therefore, it is necessary for a Ralph maintainers to have their development
tools properly configured. For the details, see the [Maintainer's development tools][3]
section.

Like the rest of the package management operations, releasing and publishing a
new version is automated and does not require specific environment to be
performed.

The process of releasing and publishing a new version is the following:

1. Switch to `ng` branch and ensure it is clean:
    ```
    git checkout ng
    git status
    ```
2. Pull the latest changes from the ng branch of the [upstream repository][1]:
    ```
    git pull upstream ng
    ```
3. Generate a Debian changelog and edit it as required:
   ```
   make release-new-version
   ```
4. Enter your `gpg` key password, if asked, to sign the commit and the tag.
5. Verify the changelog in `debian/changelog` contains the latest changes
   committed:
   ```
   head debian/changelog
   ```
6. Verify the version in the latest commit message is correct and the commit
   is tagged:
   ```
   git log
   ```
7. Verify signatures for both the latest commit and for its tag:
   ```
   git verify-commit HEAD
   git verify-tag <LATEST_TAG>
   ```
8. Push the latest commit along with the tag to the `ng` branch of the upstream
   repository:
   ```
   git push upstream ng --follow-tags
   ```
9. Create a new GitHub release.
10. Verify the job succeeded and the packagecloud repository contains the
   [built version][2].


## The ecosystem

The general idea behind the package maintainers' tools is that every operation
should not require specific environment to perform it in. Therefore a developer
is able to build and test a package or to release a new version using just the
tools a regular Ralph developer already has. This required introducing a few
compromises:

* Everything is done in docker containers to avoid forcing developers to
  install Ubuntu
* Since IO performance for docker mounted volumes experiences severe problems
  on certain platforms, containers are built every time a package maintenance
  operation is performed.
* Official Ralph repository is owned by [Allegro] and is  hosted
  in packagecloud. Package publishing action is triggered by publishing
  a new release in Ralph GitHub repository. This is done by maintainers
  with sufficient repository access rights.


## Building packages

Building Ralph package can be done in two modes: snapshot and release. Those
modes produce packages for testing and for production uses respectively. The
Makefile available in Ralph provides a target for each of the modes.


### Building snapshot packages

Snapshot packages can be built for any commit and are meant to be used for
either developers or a CI to test some code or configuration changes. In order
to build a snapshot package run:

```bash
make build-snapshot-package
```

The built package will be put into the `build` catalog and will have the name
that will look like `ralph-core_<DATE>.<PATCH>-<BRANCH>-SNAPSHOT_amd64.deb`.


### Building release packages

Release packages are meant to be used on production therefore they should be
built from the tagged HEAD of the `ng` branch. This, however, is not strictly
controlled by the tool chain to handle different edge cases.

In order to build a release package run:

```bash
make build-package
```

 > If a release package is meant to be published, a maintainer should manually
 > create a new GitHub release.

[1]: https://github.com/allegro/ralph
[2]: https://packagecloud.io/allegro/ralph
[3]: ./maintainers_devtools.md
[packagecloud]: https://packagecloud.io
[Ubuntu]: https://ubuntu.com
[Debian]: https://debian.org
[Allegro]: https://allegro.pl
