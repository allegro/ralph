#! /bin/bash

set -uex

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "${SCRIPT_DIR}/.."

dpkg-buildpackage -us -uc

