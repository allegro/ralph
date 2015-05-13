#!/bin/bash

pip install -r requirements/base.txt
pip install -r requirements/dev.txt
pip install -r requirements/test.txt
(
	echo "DROP DATABASE IF EXISTS ralph_ng; CREATE DATABASE ralph_ng;"
	echo "GRANT ALL PRIVILEGES ON ralph_ng TO 'ralph_ng'@'%' WITH GRANT OPTION;"
	echo "FLUSH PRIVILEGES;"
) | mysql -uroot -proot
rm src/ralph/{assets,back_office,data_center}/migrations -Rf
ralph makemigrations assets
ralph migrate
# add user root
ralph loaddata users.json
