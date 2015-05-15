#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..
pip install -r requirements/dev.txt
(
	echo "DROP DATABASE IF EXISTS ralph_ng; CREATE DATABASE ralph_ng;"
	echo "USE ralph_ng; GRANT ALL PRIVILEGES ON ralph_ng TO 'ralph_ng'@'%' WITH GRANT OPTION;"
	echo "FLUSH PRIVILEGES;"
) | mysql -uroot
rm src/ralph/{assets,back_office,data_center,licences,supports}/migrations -Rf
ralph makemigrations {assets,back_office,data_center,licences,supports}
ralph migrate
# add user root
ralph loaddata $DIR/users.json
# generate DB schema dump to image
#dev_ralph graph_models assets -a -o models_relations.png
