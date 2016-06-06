#!/bin/bash

set -e

[[ $(ralph makemigrations --dry-run) =~ "No changes detected" ]]
