FROM node:8.12 as build-static

WORKDIR /opt/ralph_static

COPY package.json gulpfile.js bower.json ./
COPY src/ralph/static/src/ ./src/ralph/static/src/
COPY src/ralph/admin/static/ ./src/ralph/admin/static/
RUN npm install --silent -g bower && \
    npm install --silent -g gulp && \
    npm install --silent && \
    bower --allow-root install && \
    gulp build


FROM python:3.6-stretch

ARG RALPH_ROOT=/opt/ralph
ARG STATIC_ROOT=/opt/static

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1
ENV LANG C.UTF-8

WORKDIR ${RALPH_ROOT}

RUN apt-get update -qq && \
    apt-get install -y -q build-essential \
                          libldap2-dev \
                          libsasl2-dev \
    && \
    apt-get autoremove -y && \
    apt-get clean && \
    apt-get autoclean && \
    echo -n > /var/lib/apt/extended_states && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /usr/share/man/?? && \
    rm -rf /usr/share/man/??_*

COPY . .
COPY --from=build-static /opt/ralph_static/src/ralph/static/ ${STATIC_ROOT}/
COPY --from=build-static /opt/ralph_static/src/ralph/admin/static/ ${STATIC_ROOT}/
COPY --from=build-static /opt/ralph_static/bower_components/ ${STATIC_ROOT}/bower_components/
RUN pip install -e . && \
    pip install -r requirements/prod.txt
