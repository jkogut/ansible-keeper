# ansible-keeper
Keep ansible inventory in zookeeper:  http://zookeeper.apache.org/


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

Add new hosts to inventory: *[example with adding zookeeper hosts to zookeeper group]*
```
./ansibleKeeper.py -A zookeeper:zoo1.dmz
./ansibleKeeper.py -A zookeeper:zoo1.dmz
./ansibleKeeper.py -A zookeeper:zoo1.dmz
```

Add new hosts with host variables: *[example with adding flink worker hosts to flink-workers group]*
```
./ansibleKeeper.py -A flink-workers:fworker1.dmz,lan_ip4:1.1.1.1,id:1
./ansibleKeeper.py -A flink-workers:fworker2.dmz,lan_ip4:1.1.1.2,id:2
./ansibleKeeper.py -A flink-workers:fworker3.dmz,lan_ip4:1.1.1.3,id:3

```

### Check newly added groups

Use show option to check what is in zookeepers group:

```
./ansibleKeeper.py -S zookeeper
```

You should get JSON output

```
{"zoo1.dmz": {}, "zoo3.dmz": {}, "zoo2.dmz": {}}
```

Now use show option to check what is in flink-workers group:

```
./ansibleKeeper.py -S flink-workers
```

You should get JSON output

```
												  
{"fworker3.dmz": {"id": "3", "lan_ip4": "1.1.1.3"}, "fworker2.dmz": {"id": "2", "lan_ip4": "1.1.1.2"}, "fworker1.dmz": {"id": "1", "lan_ip4": "1.1.1.1"}}
```
