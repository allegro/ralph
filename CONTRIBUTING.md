# We are open :-)

Ralph is an Open Source system which allows managing data centres in an easy and straightforward manner.
We dont just provide the sources, all our development process, including planning, blueprinting, and even scrum sprints are done in public! [Flexible](/development/overview) and [adaptable](/development/addons) architecture behind the project encourages developers to experiment with their needs and expectations. How to become part of the development process ?

## In a nutshell

This is how you fix a bug or add a feature in few quick steps:

1. fork us on [GitHub](https://github.com/allegro/ralph/),
2. checkout your fork,
3. write a code (with [PEP8](https://www.python.org/dev/peps/pep-0008/) rules), test, commit,
4. push changes to your fork,
5. open a pull request.

# Becoming contributor

## Hello !

Introduce yourself at our Gitter Chat https://gitter.im/allegro/ralph, where current Ralph-related issues and concerns are aired, shared and solved.

## Development environment

Make your software compatible with Ralph development requirements.

1. First, install `git` and `Vagrant` applications.
2. Then, `git clone https://github.com/allegro/ralph`. The "ng" branch is used by Ralph 3.0, the newest version of the software, currently under development. We do not work anymore on old 2.x branch from develop branch.
4. Inside "vagrant" directory you will find Vagrantfile for setting up development environment. Just type `vagrant up` to boot up complete development environment.
5. Now log in the virtual box environment with `vagrant ssh`.
6. Virtualenv is activated automatically - shell script sits in ~/bin/activate.
7. Run `make menu`.
8. Run ralph instance with `make run`, login to the localhost:8000 using `ralph`:`ralph` creditentials.

Then, you are all set ! In case of problems with setting everything up, refer to the `https://github.com/allegro/ralph/tree/ng/vagrant`

If you want to extend Ralph by your own Django app, place your config inside
`vagrant/Vagrantfile.local` (ex. synced folders). You could also attach custom
provisioning script in `vagrant/provision.local.sh`.

## Bug tracker & sprints

Github issues tracker handles our development. We use `milestones` for our development sprints(week, or 2 weeks per milestone) with some estimated release date. Point your browser to: https://waffle.io/allegro/ralph?label=ng for Scrum board(use milestone field for filtering) for more details.

## Blueprints

We discuss every design decision on Github using so called "Blueprints". It's just an Github issue with some design drafts, diagrams and general discussion. You can recognise the blueprint by using 'blueprint' label on issues list.

## Technical documentation

Ready for coding? Please RTFM [our technical/architecture documentation](http://ralph-ng.readthedocs.org)

# Do's and don't's

## Do's

If you want a quick response, notify @vi4m on Gitter
Start your topic on Github in "issues" section. Our homepage is for general discussions.
Feel free to explore beauty of Python programming. Make contributions that matters.

## Don't's

The answer to the question "When is it ready?" is "When it is ready" :-)

## Django's template standard

There are few simple rules:

1. Blank line between ``load`` and the rest of a template.
2. Blank line between block sections.
3. If you open some HTML tag or Django template tag you must indent line, excluding simple code, self-closing tags (looking for inline block and ``{% url ... %}`` in example).
4. And the last one (the most important): when you write template, let you use common sense.

All of this is for human readability not for the browsers.

Example:
```django
{% extends 'base.html' %}
{% load i18n %}

{% block title %}{% trans 'Users' %}{% endblock %}

{% block sidebar %}
  {% if users %}
    <ul>
      {% for user in users %}
        <li>
            <a href="{% url admin:users user.pk %}">{{ user }}</a>
        </li>
      {% endif %}
    </ul>
  {% endif %}
{% endblock %}
```
