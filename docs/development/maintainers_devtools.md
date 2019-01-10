# Maintainer's development tools

Ralph does not impose certain development tools to be used along with certain
configuration in order to be a Ralph developer. Maintainers, however, are
required to have certain tools configured appropriately in order to successfully
perform some of the maintenance operations.

If you are a Ralph maintainer, please read this guide carefully.


## GnuPG

Every Ralph maintainer should have at least a 4096 bit gpg key that has a
signing capability. The key must be signed by other Ralph maintainers. The key
must have an expiration date. Setting up a key is described in [GnuPG HowTo][1].

The list of identities should include at least the given name according to an
official document and the email, specified in the git configuration.

The up-to-date public key has to be available on one of the major key servers.
In order to make the things happening faster, it's recommended to upload public
keys to Ubuntu key server at hkp://keyserver.ubuntu.com.

 > Users of [fish] and other fancy shells that play around with TTYs should set
 > appropriate value to `GPG_TTY` variable within their shell session in order
 > to be able to sign tags. Run `export GPG_TTY=$(tty)` within the current
 > session or add that line to the appropriate configuration file.


## Git

The following git configuration options has to be set either globally or
locally:

* **user.name**: Full name of the maintainer in ASCII letters according to
  the official document. It is possible to use non-ASCII Latin characters but
  some of the tools may misinterpret that.
* **user.email**: The email.
* **user.signingkey**: The ID of the GnuPG key that will be used for signing
  both commits and the tags.


## GitHub account

The list of **verified** emails has to include the email that is used in the git
configuration for creating commits.

The GnuPG public key has to be added to the account.


[1]: https://www.gnupg.org/documentation/howtos.html
[fish]: https://fishshell.com
