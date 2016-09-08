# ralph-cli

`ralph-cli` is an OpenSource tool (see [its GitHub repo][ralph-cli]), meant as a
command-line interface for Ralph. Its goal is to serve as a "Swiss Army knife"
for all the Ralph's functionality that is reasonable enough for bringing it from
web GUI to your terminal.

At this moment, you can use it for discovering components of your hardware (with
`scan` command), but we are going to extend the functionality in the future (see
[Ideas for Future Development][development-ideas]). It's worth mentioning that
`ralph-cli` also has the ability to discover MAC addresses, which is essential
if you want to deploy your hosts from Ralph (of course, you can enter all this
data to Ralph manually, but `ralph-cli` greatly facilitates this process).

If you want to start using it, please refer to [its documentation][docs] -
especially to [Quickstart][] section and maybe [Key Concepts][] section as well,
if you're interested.

In case you'd find any issues with `ralph-cli` (or if you'd have any
suggestions/ideas), please create an issue [here][issues]. If you want to
contribute some code (in what we encourage you to do!), you may want to read
[Development][] section as well (BTW, `ralph-cli` is written in Go, but uses
Python for scan scripts).

[ralph-cli]: https://github.com/allegro/ralph-cli
[development-ideas]: http://ralph-cli.readthedocs.io/en/latest/development/#ideas-for-future-development
[docs]: http://ralph-cli.readthedocs.io/en/latest/
[Quickstart]: http://ralph-cli.readthedocs.io/en/latest/quickstart/
[Key Concepts]: http://ralph-cli.readthedocs.io/en/latest/concepts/
[issues]: https://github.com/allegro/ralph-cli/issues
[Development]: http://ralph-cli.readthedocs.io/en/latest/development/
