#!/bin/bash

## 
## ansible -i fetch-inventory.sh all --list-hosts
##

ZOO_ANSIBLE_PATH=path_to_ansibleKeeper

$ZOO_ANSIBLE_PATH/ansibleKeeper.py -I ansible
