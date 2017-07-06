# ansible-keeper
Keep ansible inventory in zookeeper:  http://zookeeper.apache.org/


Motivation
----------

1. No more editing of inventory files with huge amount of hosts with their hostvars
2. No more hostvars, groups, hosts lookups in `/etc/ansible/hosts` file 
3. No files, just zNodes on the distributed system
4. JSON format combined with `jq` gives you nice and pretty colorful output 
5. *Github integration (not yet implemented)* 
6. *Import/Export of ansible inventory TOML file (not yet implemented)* 


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

```
cfg.zkServers  = 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'
cfg.aPath      = '/ansible-test'
```


Tests
-----
Install `py.test` and run test_ansibleKeeper

It will fail in case of inaccesible zookeeper servers

```
py.test -v -l test_ansibleKeeper.py
```


Usage
-----

### Read the manual
run `./ansibleKeeper.py -h` and read the help 

### Add some hosts

Use *-A groupname1:newhostname1* to add new hosts to inventory: 

*[example with adding zookeeper hosts to zookeeper group]*
```
./ansibleKeeper.py -A zookeeper:zoo1.dmz
./ansibleKeeper.py -A zookeeper:zoo1.dmz
./ansibleKeeper.py -A zookeeper:zoo1.dmz
```

Use *-A groupname1:newhostname1,var1:value1,var2:value2,var3:value3* to add new hosts with host variables to inventory: 

*[example with adding flink worker hosts to flink-workers group]*
```
./ansibleKeeper.py -A flink-workers:fworker1.dmz,lan_ip4:1.1.1.1,id:1
./ansibleKeeper.py -A flink-workers:fworker2.dmz,lan_ip4:1.1.1.2,id:2
./ansibleKeeper.py -A flink-workers:fworker3.dmz,lan_ip4:1.1.1.3,id:3
```

### Show newly added groups

Use *-S zookeeper* option to show what is in zookeeper group:

```
./ansibleKeeper.py -S zookeeper
```

You should get JSON output

```
{"zoo1.dmz": {}, "zoo3.dmz": {}, "zoo2.dmz": {}}
```

Use *-S flink-workers* option to show what is inside flink-workers group:

```
./ansibleKeeper.py -S flink-workers
```

You should get JSON output

```											  
{"fworker3.dmz": {"id": "3", "lan_ip4": "1.1.1.3"}, "fworker2.dmz": {"id": "2", "lan_ip4": "1.1.1.2"}, "fworker1.dmz": {"id": "1", "lan_ip4": "1.1.1.1"}}
```

### Rename group and host

Use *-R groups:oldgroupname:newgroupname* option to rename zookeeper group:

```
./ansibleKeeper.py -R groups:zookeeper:zookeepers
```

Use *-R hosts:oldhostname:newhostname* option to rename fworker1.dmz host:

```
./ansibleKeeper.py -R hosts:fworker1.dmz:flink-worker1.dmz
```

### Update host variables

Use *-U groupname1:hostname1,var1:newvalue1,var2:newvalue2* option to update host variables:

*[example for host fworker2.dmz: update lan_ip4 variable with new IP 1.1.1.20]*

```
./ansibleKeeper.py -U groups:flink-workers:fworker2.dmz,lan_ip4:1.1.1.20
```

### Run ansibleKeeper.py with ansible

List all hosts with ansible

```
ansible -i fetch-inventory.sh all --list-hosts
```


List all hosts in zookeeper group with ansible

```
ansible -i fetch-inventory.sh zookeeper --list-hosts
```

Check `uptime` as a user `root`:

```
ansible -i fetch-inventory.sh zookeeper -a "uptime" -u root

  zoo3.dmz | SUCCESS | rc=0 >>
    12:20:29 up 65 days, 16:42,  1 user,  load average: 0.00, 0.01, 0.05
 
  zoo2.dmz | SUCCESS | rc=0 >>
    12:20:48 up 65 days, 16:42,  1 user,  load average: 0.00, 0.01, 0.05
  
  zoo1.dmz | SUCCESS | rc=0 >>
    12:20:43 up 70 days, 16:51,  1 user,  load average: 0.00, 0.01, 0.05
```
