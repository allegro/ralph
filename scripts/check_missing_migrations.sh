#!/bin/bash

set -e

output=$(test_ralph makemigrations --dry-run)
echo $output
[[ $output =~ "No changes detected" ]]
