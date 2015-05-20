##!/bin/bash
set -e

cd $RALPH_DIR
make docs
ralph migrate
ralph collectstatic -l --noinput

