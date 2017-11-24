#!/bin/bash

set -e
if [ ! -z "$TRAVIS" ]; then
    export DATABASE_NAME="test_$DATABASE_NAME"
fi
output=$(test_ralph makemigrations --dry-run)
echo $output
[[ $output =~ "No changes detected" ]]
