#!/bin/bash

# apply ralph config
echo "
# set STRICT_TRANS_TABLES to allow only valid values for column type
# check https://dev.mysql.com/doc/refman/5.6/en/sql-mode.html#sqlmode_strict_trans_tables for details
[mysqld]
sql_mode=NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES
" | sudo tee --append /etc/mysql/conf.d/ralph.cnf > /dev/null

sudo service mysql restart

echo "CREATE DATABASE ralph_ng DEFAULT CHARACTER SET 'utf8'" | mysql -u root
echo "GRANT ALL ON ralph_ng.* TO ralph_ng@'%' IDENTIFIED BY 'ralph_ng'; FLUSH PRIVILEGES" | mysql -u root

/home/vagrant/bin/ralph migrate

/home/vagrant/bin/ralph createsuperuser --noinput --username ralph --email ralph@allegrogroup.com
/home/vagrant/bin/python vagrant/provisioning_scripts/createsuperuser.py

cd /home/vagrant/src/ralph
make menu
