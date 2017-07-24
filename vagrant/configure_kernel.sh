#!/bin/bash

set -eu

sed -i -e "s/GRUB_CMDLINE_LINUX=\"\"/GRUB_CMDLINE_LINUX=\"net.ifnames=0 biosdevname=0\"/g" "/etc/default/grub"
update-grub
