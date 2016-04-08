#!/bin/env python
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Add VM bootable via iPXE.')
parser.add_argument('vm', type=int, help='an integer')
args = parser.parse_args()


def vboxmanage(command):
    return subprocess.check_output('vboxmanage {}'.format(command), shell=True)

name = 'pxe-node-{}'.format(args.vm)
vboxmanage(
    'createvm --name {} --register --ostype Ubuntu_64'.format(name)
)
vboxmanage(
    'modifyvm {} --memory 512 --boot1 dvd --boot2 net --nic1 hostonly --nic2 nat --hostonlyadapter1 vboxnet0'.format(name)  # noqa
)
vboxmanage(
    'storagectl {} --add ide --name test --bootable on'.format(name)
)
vboxmanage(
    'storageattach {} --storagectl test --medium ipxe.iso --port 0 --device 0 --type dvddrive'.format(name)  # noqa
)
