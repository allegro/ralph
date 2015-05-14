#!/bin/bash

echo "CREATE DATABASE ralph_ng DEFAULT CHARACTER SET 'utf8'" | mysql -u root
echo "GRANT ALL ON ralph_ng.* TO ralph_ng@'%' IDENTIFIED BY 'ralph_ng'; FLUSH PRIVILEGES" | mysql -u root

/home/vagrant/bin/ralph migrate
/home/vagrant/bin/ralph createsuperuser --noinput --username ralph --email ralph@allegrogroup.com
/home/vagrant/bin/python vagrant/provisioning_scripts/createsuperuser.py
