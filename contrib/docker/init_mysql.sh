#!/bin/bash
mysql_install_db

mysqld_safe & 
echo 'Waiting 10 secs for mysqld to come up'
sleep 10
echo "CREATE DATABASE ralph DEFAULT CHARACTER SET 'utf8'" | mysql && \
echo "GRANT ALL ON ralph.* TO ralph@'%' IDENTIFIED BY 'ralph'; FLUSH PRIVILEGES" | mysql
python createsuperuser.py
killall mysqld_safe
