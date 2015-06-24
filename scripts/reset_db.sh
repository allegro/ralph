#!/bin/bash
(
	echo "DROP DATABASE IF EXISTS ralph_ng; CREATE DATABASE ralph_ng DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;"
	echo "USE ralph_ng; GRANT ALL PRIVILEGES ON ralph_ng TO 'ralph_ng'@'%' WITH GRANT OPTION;"
	echo "FLUSH PRIVILEGES;"
) | mysql -uroot
