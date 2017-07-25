# ansible-keeper
Keep ansible inventory in zookeeper:  http://zookeeper.apache.org/


### Table of Contents
**[Motivation](#motivation)**<br>
**[Install](#install)**<br>
**[Config](#config)**<br>
**[Tests](#tests)**<br>
**[Usage](#usage)**<br>


Motivation
----------

1. No more editing of inventory files with huge amount of hosts with their hostvars
2. No more hostvars, groups, hosts lookups in `/etc/ansible/hosts` file 
3. No files, just zNodes on the distributed system
4. JSON format combined with `jq` gives you nice and pretty colorful output 
5. *Github integration (not yet implemented)* 
6. *Import/Export of ansible inventory TOML file (not yet implemented)* 
7. *AWS Dynamic inventory integration (not yet implemented)* 

Install
-------

ansible-keeper:
```
git clone git@github.com:jkogut/ansible-keeper.git
```

kazoo:
```
pip install kazoo
```


Config
------
Edit `config section` in ansibleKeeper.py file, 
and provide a list of your zookeeper servers with base znode for ansible-keeper.


Defaults:

```python
cfg.zkServers  = 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'
cfg.aPath      = '/ansible-test'
```


Tests
-----
Install `py.test` and run test_ansibleKeeper.
Test will check your zookeeper cluster connectivity and `ansibleKeeper.py` code.  

```python
py.test -v -l test_ansibleKeeper.py

============================================ test session starts =================================================
platform linux2 -- Python 2.7.12 -- py-1.4.26 -- pytest-2.6.4 -- /usr/bin/python
collected 18 items 

test_ansibleKeeper.py::TestConfig::test_zkClusterUp PASSED
test_ansibleKeeper.py::TestConfig::test_configZkClusterConnection PASSED
test_ansibleKeeper.py::TestConfig::test_configZkServerConnection PASSED
test_ansibleKeeper.py::TestConfig::test_configBasePrefixZnode PASSED
test_ansibleKeeper.py::TestReadWrite::test_addHostWithHostvars PASSED
test_ansibleKeeper.py::TestReadWrite::test_addHostToGroup PASSED
test_ansibleKeeper.py::TestReadWrite::test_deleteZnodeRecur PASSED
test_ansibleKeeper.py::TestReadWrite::test_deleteZnodeHostExistance PASSED
test_ansibleKeeper.py::TestReadWrite::test_deleteZnodeHostInGroupExistance PASSED
test_ansibleKeeper.py::TestReadWrite::test_deleteZnodeRecurGroup PASSED
test_ansibleKeeper.py::TestReadWrite::test_showHostVarsOneHost PASSED
test_ansibleKeeper.py::TestReadWrite::test_showHostVarsMultipleHosts PASSED
test_ansibleKeeper.py::TestReadWrite::test_updateSingleZnode PASSED
test_ansibleKeeper.py::TestReadWrite::test_renameHostname PASSED
test_ansibleKeeper.py::TestReadWrite::test_renameGroupname PASSED
test_ansibleKeeper.py::TestSplitters::test_splitZnodeString PASSED
test_ansibleKeeper.py::TestSplitters::test_splitZnodeVarString PASSED
test_ansibleKeeper.py::TestSplitters::test_splitRenameZnodeVarString PASSED

======================================== 18 passed in 1.26 seconds ==============================================
```


Usage
-----

### Read the manual
Run `./ansibleKeeper.py -h` and read the help. 
```
Usage: ansibleKeeper.py [opts] <args>

Options:
  --version    show program's version number and exit
  -h, --help   show this help message and exit
  -A A         add host with hostvars:
	           <groupname1:newhostname1,var1:value1,var2:value2,var3:value3>
  -G G         add host to hostgroup: <groupname:hostname>
  -D D         delete host or group recursively: <groupname1:hostname1> or
	           <groupname1> or <hosts:hostname1>
  -U U         update host variables with comma separated hostvars:
               <groupname1:hostname1,var1:newvalue1,var2:newvalue2>
  -R R         rename existing hostname or groupname:
               <groups:oldgroupname:newgroupname> or
			   <hosts:oldhostname:newhostname>
  -S S         show host variables for a given host or group:
               <groupname1:hostname1> or <groupname1>
  -I I         inventory mode: groups|all|ansible dumps inventory in json
               format from zookeeper
  --host=HOST  ansible compliant option for hostvars access: --host hostname
```


### Add some hosts

Use **-A groupname1:newhostname1** to add new hosts to inventory: 

*[example with adding zookeeper hosts to zookeeper group]*
```
./ansibleKeeper.py -A zookeeper:zoo1.dmz
./ansibleKeeper.py -A zookeeper:zoo1.dmz
./ansibleKeeper.py -A zookeeper:zoo1.dmz
```

Use **-A groupname1:newhostname1,var1:value1,var2:value2,var3:value3** to add new hosts with host variables to inventory: 

*[example with adding flink worker hosts to flink-workers group]*
```
./ansibleKeeper.py -A flink-workers:fworker1.dmz,lan_ip4:1.1.1.1,id:1
./ansibleKeeper.py -A flink-workers:fworker2.dmz,lan_ip4:1.1.1.2,id:2
./ansibleKeeper.py -A flink-workers:fworker3.dmz,lan_ip4:1.1.1.3,id:3
```


### Show newly added groups

Use **-S zookeeper** option to show what is in zookeeper group:

```
./ansibleKeeper.py -S zookeeper
```

You should get JSON output:

```
{"zoo1.dmz": {}, "zoo3.dmz": {}, "zoo2.dmz": {}}
```

Use **-S flink-workers** option to show what is inside flink-workers group:

```
./ansibleKeeper.py -S flink-workers
```

You should get JSON output:

```
{"fworker3.dmz": {"id": "3", "lan_ip4": "1.1.1.3"}, "fworker2.dmz": {"id": "2", "lan_ip4": "1.1.1.2"}, "fworker1.dmz":{"id": "1", "lan_ip4": "1.1.1.1"}}
```


### Rename group and host

Use **-R groups:oldgroupname:newgroupname** option to rename zookeeper group:

```
./ansibleKeeper.py -R groups:zookeeper:zookeepers
```

Use **-R hosts:oldhostname:newhostname** option to rename fworker1.dmz host:

```
./ansibleKeeper.py -R hosts:fworker1.dmz:flink-worker1.dmz
```


### Update host variables

Use **-U groupname1:hostname1,var1:newvalue1,var2:newvalue2** option to update host variables:

*[example for host fworker2.dmz: update lan_ip4 variable with new IP 1.1.1.20]*

```
./ansibleKeeper.py -U groups:flink-workers:fworker2.dmz,lan_ip4:1.1.1.20
```


### Add host to another group

Use **-G newgroupname:hostname** option to add host to another group.
If group exists it will add the host only otherwise it will create new group.

```
./ansibleKeeper.py -G new-flinkgroup:fworker2.dmz
```


### Run ansibleKeeper.py with ansible

You can run `ansibleKeeper.py` with ansible in one of two ways:


1. **Use** `ansible -i` option to point to your zookeeper based inventory:

List all hosts in zookeeper group with ansible pointing inventory with `-i` option:

```
ansible -i fetch-inventory.sh zookeeper --list-hosts

  hosts (3):
	zoo3.dmz
	zoo1.dmz
	zoo2.dmz
```

2. **Use** default `/etc/ansible/hosts` inventory file to point to zookeeper based inventory:

Update `fetch-inventory.sh` script with `ansibleKeeper.py` path and copy it to `/etc/ansible/hosts` and `chmod +x` it.
Run it with `ansible --list all` command as you would normally.

List all hosts in zookeeper group with ansible:

```
ansible zookeeper --list-hosts

  hosts (3):
	zoo3.dmz
	zoo1.dmz
	zoo2.dmz
```


### Check inventory hostvars with ansible

Use ansible debug module to check hostvars with ansible:

```python
ansible fworker2.dmz -m debug -a "var=lan_ip4"
fworker2.dmz | SUCCESS => {
    "lan_ip4": "1.1.1.2"
	}
```


### Inventory dump

You can see at any time structure of your infrastructure like: **list of all hosts, groups and hosts with groups** 
using inventory dump options.

**Use** `-I hosts` option to obtain sorted list of all hosts in the inventory.

```python
ansibleKeeper.py -I hosts| jq
[
	"fworker1.dmz",
	"fworker2.dmz",
	"fworker3.dmz",
	"zoo1.dmz",
	"zoo2.dmz",
	"zoo3.dmz"
]
```

**Use** `-I groups` option to obtain sorted list of all groups in the inventory.

```python
ansibleKeeper.py -I groups| jq
[
	"flink-workers",
	"zookeeper"
]
```

**Use** `-I all` option to obtain sorted list of all groups and hosts in the inventory.

```python
ansibleKeeper.py -I all| jq
{
  "hosts": [
	"fworker1.dmz",
	"fworker2.dmz",
	"fworker3.dmz",
	"zoo1.dmz",
	"zoo2.dmz",
	"zoo3.dmz"
	],
  "groups": [
	{
		"flink-workers": [
			"fworker1.dmz",
			"fworker2.dmz",
			"fworker3.dmz"
		]
	},
		"zookeeper": [
			"zoo1.dmz",
			"zoo2.dmz",
			"zoo3.dmz"
		]
	}
  ]
}
```		
