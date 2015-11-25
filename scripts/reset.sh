#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/..
#pip install -r requirements/dev.txt
./scripts/reset_db.sh
rm -Rf src/ralph/{accounts,assets,attachments,lib/transitions,back_office,data_center,licences,supports,reports,data_importer,domains}/migrations
ralph makemigrations {accounts,assets,attachments,back_office,data_center,licences,supports,transitions,reports,data_importer,domains}
ralph migrate
# add user root
#ralph loaddata $DIR/users.json
# generate DB schema dump to image
#dev_ralph graph_models assets -a -o models_relations.png
