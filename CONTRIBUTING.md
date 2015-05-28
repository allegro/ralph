# Getting involved

Ralph is an Open Source system which allows managing data centres in an easy and straightforward manner. Flexible and adaptable architecture behind it encourages developers to experiment with their needs and expectations. How to become part of the development process ?

# Becoming contributor

## Hello !
Introduce yourself at our Gitter Chat, where current Ralph-related issues and concerns are aired, shared and solved.

## Development environment
Make your software compatible with Ralph development requirements.
First, install `git` and `Vagrant` applications.
Then, `git clone https://github.com/allegro/ralph`.
The "ng" branch is used by Ralph 3.0, the newest version of the software, currently under development.
Inside "vagrant" directory you will find Vagrantfile for setting up development environment. Just type `vagrant up` to boot up complete development environment.
Now log in the virtual box environment with `vagrant ssh`.
Run ralph instance with `source ~/bin/activate && ralph runserver 0.0.0.0:8000`
Then, you are all set ! For more information go to `https://github.com/allegro/ralph/tree/ng/vagrant`

## Bug tracker.
Github issues tracker handles our development. We use `milestones` for our development sprints(week, or 2 weeks per milestone) with some estimated release date.

## Blueprints
We discuss every design decision on Github using so called "Blueprints". It's just an Github issue with some design drafts, diagrams and general discussion. You can recognise the blueprint by using 'blueprint' label.


# Do's and don't's

## Do's

If you want a quick response, notify @vi4m on Gitter
Start your topic on Github in "issues" section. Our homepage is for general discussions.
Feel free to explore beauty of Python programming. Make contributions that matters.

## Don't's

The answer to the question "When is it ready?" is "When it is ready".


# Finding your way around the sources

## Concept

The entire application is based on highly operational django models. Django framework generates user interface forms on its own. As simplicity is our main concern, we prefer to keep the models fat and user interface thin. That's why we rely on Django admin panel for managing user interface.

## Main modules

Ralph is divided into separate models, such as:
- Assets - storing a wide array of information about fixed assets
- Scan - discovering equipment of data centres
- Licenses - managing licenses for both software and hardware
- CMDB - configuration management database
