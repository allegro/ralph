FROM ubuntu:14.04
MAINTAINER PyLabs pylabs@allegrogroup.com

# basic provisioning
ADD docker/provision.sh /root/provision.sh
RUN /root/provision.sh

# additional scripts
ADD docker/init.sh /root/init.sh
ADD docker/upgrade.sh /root/upgrade.sh

# install ralph
ENV RALPH_DIR /opt/ralph
ADD . $RALPH_DIR
WORKDIR $RALPH_DIR
RUN make install-dev  # temporary
RUN make docs

VOLUME ["/opt/ralph/docs"]
CMD ["ralph", "runserver", "0.0.0.0:8000"]
