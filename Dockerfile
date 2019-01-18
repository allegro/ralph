FROM ubuntu:bionic
MAINTAINER PyLabs pylabs@allegro.pl

# set UTF-8 locale
RUN apt-get clean && apt-get update
RUN apt-get install locales
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# set paths
ENV RALPH_DIR=/opt/ralph
ENV RALPH_EXEC=ralph
ENV RALPH_LOGGING_FILE_PATH=/root/logs/runtime.log
ENV RALPH_STATIC=/root/static
ENV SCRIPTS_PATH=/root

ADD docker/* $SCRIPTS_PATH/

# basic provisioning
RUN $SCRIPTS_PATH/provision.sh

# npm provisioning
ADD package.json $RALPH_DIR/package.json
RUN $SCRIPTS_PATH/provision_js.sh

# cleanup
RUN apt-get clean

# install basic requirements
WORKDIR $RALPH_DIR
ADD requirements $RALPH_DIR/requirements
ADD Makefile $RALPH_DIR/Makefile
# don't install ralph now - only requirements
RUN sed -i '/\-e ./d' $RALPH_DIR/requirements/test.txt
# temporary - change to `make install-prod` finally
RUN make install-dev

# install JS dependencies
ADD src/ralph/admin/static $RALPH_DIR/src/ralph/admin/static
ADD src/ralph/static $RALPH_DIR/src/ralph/static
ADD gulpfile.js bower.json package.json $RALPH_DIR/
RUN $SCRIPTS_PATH/init_js.sh

# install ralph
ADD . $RALPH_DIR
RUN pip3 install -e .

VOLUME $RALPH_STATIC
CMD $RALPH_EXEC runserver 0.0.0.0:8000
