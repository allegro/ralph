FROM ubuntu:14.04
MAINTAINER PyLabs pylabs@allegrogroup.com

# set UTF-8 locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# basic provisioning
ENV SCRIPTS_PATH=/root
ADD docker/provision.sh $SCRIPTS_PATH/provision.sh
RUN /root/provision.sh

# add additional scripts
ADD docker/* $SCRIPTS_PATH/

# set paths
ENV RALPH_DIR=/opt/ralph
ENV RALPH_EXEC=ralph
ENV RALPH_LOGGING_FILE_PATH=$RALPH_PATH/logs/runtime.log
ENV RALPH_STATIC=/root/static
ENV RALPH_DOCS=$RALPH_DIR/docs

# install ralph
ADD . $RALPH_DIR
WORKDIR $RALPH_DIR
RUN $SCRIPTS_PATH/init_js.sh
RUN make install-dev  # temporary
RUN make docs

VOLUME $RALPH_DOCS
VOLUME $RALPH_STATIC
CMD $RALPH_EXEC runserver 0.0.0.0:8000
