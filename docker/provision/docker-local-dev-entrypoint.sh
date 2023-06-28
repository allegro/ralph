#!/bin/bash
set -e
pip3 install -r /var/local/ralph/requirements/dev.txt
cd /var/local/ralph
make run
