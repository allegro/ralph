# Deb package for Ubuntu

The way Ralph is made makes changing versions of its dependencies challenging
so in order to provide a deb package for [Ubuntu] it is necessary to use 
`dh_virtualenv` which installs all dependencies into a virtualenv and packs
the latter into a package. Although this approach is not blessed by either
[Debian] or Ubuntu maintainers, it provides a healthy compromise between the
availability of the Ralph package and the effort required to make one.

The package is built and published to [Bintray] by the Ralph core maintainers.
This document describes what is necessary to know and to have for a maintainer
to be able to build, test and publish the package.


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
* Official Ralph repository is owned by [Allegro], so publishing a package
  requires sharing Allegro's credentials for Bintray which according to their
  policy cannot be done. Therefore the script for that is going to only be
  present in the CI system that is available to maintainers inside Allegro.


## Building packages

Building Ralph package can be done in two modes -- snapshot and release. Those
modes produce packages for testing and for production uses respectively. The
Makefile available in Ralph provides a target for each of the modes.


### Building snapshot packages

Snapshot packages can be built for any commit and are meant to be used for
either developers or a CI to test some code or configuration changes. In order
to build a snapshot package run:

```bash
make build-snapshot-package
```

The built package will be put into the build catalog and will have the name
that will look like ``.


### Building release packages

Release packages are meant to be used on production therefore they should be
build from the tagged HEAD of the `ng` branch. This, however, is not strictly
controlled by the toolchain to handle different edge cases.

In order to build a release package run:

```bash
make build-package
```

 > If a release package is meant to be released, a maintainer should release
 > a new version prior to building one. The way to do that is described bellow.


## Releasing and publishing new versions

Properly releasing versions is one of the key duties of every Ralph maintainer.

Like the rest of the package management operations releasing and publishing a
new version is automated and does not require specific environment to be
performed.

However, it is necessary for a Ralph maintainer to have their development tools
properly configured, in order to release and sign packages.

 > Prior to releasing a version make sure the development tools are set up.
 > For the details, see the [Maintainer's development tools][3] section.

The process of releasing and publishing a new version is the following:

1. Switch to `ng` branch and ensure it is clean.
2. Pull the latest changes from the ng branch of the [upstream repository][1].
3. Run `make release-new-version`.
   This will generate a debian changelog based on git commits and will open
   it in vim-tiny for a final examination.
4. Edit the changelog as required, save the file and quit the editor.
5. At this point `gpg` may ask for a password once or twice in order to sign
   both the commited changelog and the created tag.
5. Verify the changelod in `debian/changelog` contains the latest changes
   commited.
6. Verify the version in the latest commit message is correct.
7. Verify the latest commit is tagged.
6. Verify signatures for both the latest commit and for its tag.
7. [Optional] Verify you can build a *release* package.
7. Push the latest commit along with the tag to the `ng` branch of the upstream
   repository. To do that run `git push upstream ng --follow-tags`.
8. Log in to the CI used for publishing Ralph packages and run
   `release-new-version` job.
9. Verify the job succeeded and the Bintray repository contains the
   [built version][2]


[1]: https://github.com/allegro.ralph
[2]: https://dl.bintray.com/vi4m/ralph/dists/bionic/main/binary-amd64/
[3]: ./maintainers_devtools.md
[Bintray]: https://bintray.com
[Ubuntu]: https://ubuntu.com
[Debian]: https://debian.org
[Allegro]: https://allegro.pl
