# Ralph
#
# VERSION               2.0.0-3

FROM      ubuntu:14.04
MAINTAINER Marcin Kliks marcin.kliks@allegro.pl

RUN apt-get update
RUN apt-get install -y python2.7 python-dev python-virtualenv build-essential libbz2-dev libfreetype6-dev libgdbm-dev libxft-dev
RUN apt-get install -y libjpeg-dev libldap2-dev libltdl-dev libmysqlclient-dev libreadline-dev libsasl2-dev libsqlite3-dev
RUN apt-get install -y libssl-dev libxslt1-dev ncurses-dev zlib1g-dev
RUN apt-get install -y libcap2-bin 
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y redis-server mysql-server libmysqlclient-dev libmysqld-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y openssh-server apache2 supervisor
RUN apt-get install -y git
ADD init_mysql.sh /root/init_mysql.sh
RUN sh /root/init_mysql.sh
#RUN echo 'alter database ralph character set utf8 collate utf8_polish_ci' | mysql -u root 
RUN pip install -U pip
RUN pip install -U flake8
RUN git clone http://github.com/allegro/ralph.git /root/ralph-git/ralph
RUN cd /root/ralph-git/ralph; make install 
RUN ralph makeconf
ADD settings /.ralph/additional-settings
ADD createsuperuser.py /root/createsuperuser.py
RUN cat /.ralph/additional-settings >>/.ralph/settings
RUN /usr/bin/mysqld_safe & \
    sleep 10 && \
    ralph syncdb --all --noinput && \
    ralph migrate --fake && \
    ralph createsuperuser ralph --noinput --user ralph --email ralph@allegrogroup.com && \
    python /root/createsuperuser.py && \
    ralph collectstatic -l --noinput
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000 22

CMD ["/usr/bin/supervisord"]

