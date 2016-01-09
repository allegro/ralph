FROM ubuntu:14.04
MAINTAINER PyLabs pylabs@allegrogroup.com

# set UTF-8 locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# set paths
ENV RALPH_DIR=/opt/ralph
ENV SCRIPTS_PATH=/root
ENV RALPH_STATIC=/root/static
ENV RALPH_DOCS=$RALPH_DIR/docs

ENV PIP_WHEEL_DIR=/wheels
ENV PIP_FIND_LINKS=/wheels

RUN apt-get update && apt-get install -y --no-install-recommends libmysqlclient-dev
RUN apt-get install -y --no-install-recommends wget && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && python3 get-pip.py && rm get-pip.py && apt-get -y purge wget && apt-get -y autoremove

ADD docker/* $SCRIPTS_PATH/
ADD wheels /wheels

WORKDIR $RALPH_DIR
RUN pip3 install --no-index -f $PIP_WHEEL_DIR/wheels $(ls $PIP_WHEEL_DIR/wheels/*.whl)

VOLUME $RALPH_DOCS
VOLUME $RALPH_STATIC
CMD $RALPH_EXEC runserver 0.0.0.0:8000
