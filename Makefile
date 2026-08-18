TEST?=ralph
TEST_ARGS=
DOCKER_REPO_NAME?=allegro
DOCKER?=docker
RALPH_VERSION?=$(shell git describe --abbrev=0)

.PHONY: test flake clean coverage coveralls

# release-new-version is used by ralph mainteiners prior to publishing
# new version of the package. The command generates the debian changelog
# commits it and tags the created commit with the appropriate snapshot version.
release-new-version: new_version = $(shell ./get_version.sh generate)
release-new-version:
	$(DOCKER) build \
		--force-rm \
		-f docker/Dockerfile-deb \
		--build-arg GIT_USER_NAME="$(shell git config user.name)" \
		--build-arg GIT_USER_EMAIL="$(shell git config user.email)" \
		-t ralph-deb:latest .
	$(DOCKER) run --rm -it -v $(shell pwd):/volume ralph-deb:latest release-new-version
	$(DOCKER) image rm --force ralph-deb:latest
	git add debian/changelog
	git commit -m "Updated changelog for $(new_version) version."
	git tag -m $(new_version) -a $(new_version)

# build-package builds a release version of the package using the generated
# changelog and the tag.
build-package:
	$(DOCKER) build --force-rm -f docker/Dockerfile-deb -t ralph-deb:latest .
	$(DOCKER) run --rm -v $(shell pwd):/volume ralph-deb:latest build-package
	$(DOCKER) image rm --force ralph-deb:latest

# build-snapshot-package renerates a snapshot changelog and uses it to build
# snapshot version of the package. It is mainly used for testing.
build-snapshot-package:
	$(DOCKER) build --force-rm -f docker/Dockerfile-deb -t ralph-deb:latest .
	$(DOCKER) run --rm -v $(shell pwd):/volume ralph-deb:latest build-snapshot-package
	$(DOCKER) image rm --force ralph-deb:latest

build-docker-image:
	$(DOCKER) build \
		--no-cache \
		-f docker/Dockerfile-prod \
		--build-arg RALPH_VERSION="$(RALPH_VERSION)" \
		-t $(DOCKER_REPO_NAME)/ralph:latest \
		-t "$(DOCKER_REPO_NAME)/ralph:$(RALPH_VERSION)" .
	$(DOCKER) build \
		-f docker/Dockerfile-inkpy \
		-t "$(DOCKER_REPO_NAME)/inkpy:$(RALPH_VERSION)" .
	$(DOCKER) build \
		--no-cache \
		-f docker/Dockerfile-static \
		--build-arg RALPH_VERSION="$(RALPH_VERSION)" \
		-t $(DOCKER_REPO_NAME)/ralph-static-nginx:latest \
		-t "$(DOCKER_REPO_NAME)/ralph-static-nginx:$(RALPH_VERSION)" .

build-snapshot-docker-image: version = $(shell ./get_version.sh show)
build-snapshot-docker-image: build-snapshot-package
	$(DOCKER) build \
		-f docker/Dockerfile-prod \
		--build-arg RALPH_VERSION="$(version)" \
		--build-arg SNAPSHOT="1" \
		-t $(DOCKER_REPO_NAME)/ralph:latest \
		-t "$(DOCKER_REPO_NAME)/ralph:$(version)" .
	$(DOCKER) build \
		-f docker/Dockerfile-inkpy \
		-t "$(DOCKER_REPO_NAME)/inkpy:$(version)" .
	$(DOCKER) build \
		-f docker/Dockerfile-static \
		--build-arg RALPH_VERSION="$(version)" \
		-t "$(DOCKER_REPO_NAME)/ralph-static-nginx:$(version)" .

publish-docker-image: build-docker-image
	$(DOCKER) push $(DOCKER_REPO_NAME)/ralph:$(RALPH_VERSION)
	$(DOCKER) push $(DOCKER_REPO_NAME)/ralph:latest
	$(DOCKER) push $(DOCKER_REPO_NAME)/ralph-static-nginx:$(RALPH_VERSION)
	$(DOCKER) push $(DOCKER_REPO_NAME)/ralph-static-nginx:latest
	$(DOCKER) push $(DOCKER_REPO_NAME)/inkpy:$(RALPH_VERSION)

publish-docker-snapshot-image: version = $(shell ./get_version.sh show)
publish-docker-snapshot-image: build-snapshot-docker-image
	$(DOCKER) push $(DOCKER_REPO_NAME)/ralph:$(version)
	$(DOCKER) push $(DOCKER_REPO_NAME)/inkpy:$(version)
	$(DOCKER) push $(DOCKER_REPO_NAME)/ralph-static-nginx:$(version)

install-js:
	npm install
	./node_modules/.bin/gulp

js-hint:
	find src/ralph|grep "\.js$$"|grep -v vendor|xargs ./node_modules/.bin/jshint;

install: install-js
	pip3 install -r requirements/prod.txt

install-test:
	pip3 install -r requirements/test.txt

install-dev:
	pip3 install -r requirements/dev.txt

isort:
	isort --diff --recursive --check-only --quiet src

test: clean
	test_ralph test $(TEST) $(TEST_ARGS)

flake: isort
	flake8 src/ralph
	flake8 src/ralph/settings --ignore=F405 --exclude=*local.py
	@cat scripts/flake.txt

checks:
	ruff check src

clean:
	find . -name '*.py[cod]' -delete;

coverage: clean
	coverage run $(shell which test_ralph) test $(TEST) -v 2 --keepdb --settings="ralph.settings.test"
	coverage report

docs: install-dev
	mkdocs build

run:
	dev_ralph runserver_plus 0.0.0.0:8000

menu:
	ralph sitetree_resync_apps

translate_messages:
	ralph makemessages -a

compile_messages:
	ralph compilemessages
