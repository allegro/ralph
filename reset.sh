#!/bin/bash

pip install -r requirements/base.txt
pip install -r requirements/dev.txt
pip install -r requirements/test.txt
(
	echo "DROP DATABASE IF EXISTS ralph_ng; CREATE DATABASE ralph_ng;"
	echo "USE ralph_ng; GRANT ALL PRIVILEGES ON ralph_ng TO 'ralph_ng'@'%' WITH GRANT OPTION;"
	echo "FLUSH PRIVILEGES;"
) | mysql -uroot -proot
rm src/ralph/{assets,back_office,data_center,licences,supports}/migrations -Rf
ralph makemigrations {assets,back_office,data_center,licences,supports}
ralph migrate
# add user root
ralph loaddata users.json
ralph graph_models assets -a -o models_relations.png --settings=ralph.settings.dev
