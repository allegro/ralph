FROM ubuntu:14.04
MAINTAINER PyLabs pylabs@allegrogroup.com

# set UTF-8 locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# set paths
ENV RALPH_DIR=/opt/ralph
ENV RALPH_EXEC=ralph
ENV RALPH_LOGGING_FILE_PATH=$RALPH_PATH/logs/runtime.log
ENV RALPH_STATIC=/root/static
ENV RALPH_DOCS=$RALPH_DIR/docs
ENV SCRIPTS_PATH=/root

ADD docker/* $SCRIPTS_PATH/

# basic provisioning
RUN $SCRIPTS_PATH/provision.sh

# npm provisioning
ADD package.json $RALPH_DIR/package.json
RUN $SCRIPTS_PATH/provision_js.sh

# install ralph
ADD . $RALPH_DIR
WORKDIR $RALPH_DIR
# temporary - change to `make install-prod` finally
RUN make install-dev
RUN $SCRIPTS_PATH/init_js.sh
RUN make docs

VOLUME $RALPH_DOCS
VOLUME $RALPH_STATIC
CMD $RALPH_EXEC runserver 0.0.0.0:8000
