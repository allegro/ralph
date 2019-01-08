TEST?=ralph

.PHONY: test flake clean coverage docs coveralls

# release-new-version is used by ralph mainteiners prior to publishing
# new version of the package. The command generates the debian changelog 
# commits it and tags the created commit with the appropriate snapshot version.
release-new-version: new_version = $(shell ./get_version.sh generate)
release-new-version:
	docker build --force-rm -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run --rm -it -v $(shell pwd):/volume ralph-deb:latest release-new-version
	docker image rm --force ralph-deb:latest
	git add debian/changelog
	GIT_EDITOR=vim.tiny git commit -m "Updated changelog for $(new_version) version."
	git tag -m $(new_version) -a $(new_version) -s

# build-package builds a release version of the package using the generated
# changelog and the tag.
build-package:
	docker build --force-rm -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run --rm -v $(shell pwd):/volume ralph-deb:latest build-package
	docker image rm --force ralph-deb:latest

# build-snapshot-package renerates a snapshot changelog and uses it to build
# snapshot version of the package. It is mainly used for testing.
build-snapshot-package:
	docker build --force-rm -f docker_ng/Dockerfile-deb -t ralph-deb .
	docker run --rm -v $(shell pwd):/volume ralph-deb:latest build-snapshot-package
	docker image rm --force ralph-deb:latest

install-js:
	npm install
	bower install
	./node_modules/.bin/gulp

js-hint:
	find src/ralph|grep "\.js$$"|grep -v vendor|xargs ./node_modules/.bin/jshint;

install: install-js
	pip3 install -r requirements/prod.txt

install-test:
	pip3 install -r requirements/test.txt

install-dev:
	pip3 install -r requirements/dev.txt

install-docs:
	pip3 install -r requirements/docs.txt

isort:
	isort --diff --recursive --check-only --quiet src

test: clean
	test_ralph test $(TEST)

flake: isort
	flake8 src/ralph
	flake8 src/ralph/settings --ignore=F405 --exclude=*local.py
	@cat scripts/flake.txt

clean:
	find . -name '*.py[cod]' -exec rm -rf {} \;

coverage: clean
	coverage run $(shell which test_ralph) test $(TEST) --keepdb --settings="ralph.settings.test"
	coverage report

docs: install-docs
	mkdocs build

run:
	dev_ralph runserver_plus 0.0.0.0:8000

menu:
	ralph sitetree_resync_apps

translate_messages:
	ralph makemessages -a

compile_messages:
	ralph compilemessages
