#!/bin/bash

set -e

[[ $(test_ralph makemigrations --dry-run) =~ "No changes detected" ]]
