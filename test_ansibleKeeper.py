'''       
Tests for migrate_druid_segments_hdfs2s3.py.
'''

__author__ = "Jan Kogut"
__copyright__ = "Jan Kogut"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Jan Kogut"
__status__ = "Beta"


import pytest
from ansibleKeeper import *
from kazoo.client import KazooClient
from kazoo.handlers.threading import *


def test_zookeeperClusterConnection():
    '''
    Test if we can connect to zookeeper cluster servers.
    '''

    ## example server list string 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'
    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()
        
    assert type(zk).__name__ == 'KazooClient'

    zk.stop()


def test_zookeeperServerConnection():
    '''
    Test if we can connect to each zookeeper server.
    '''

    ## example server list string 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'

    zkSrvList = cfg.zkServers.split(',')
    
    for srv in zkSrvList:
        try:
            zk = KazooClient(hosts=srv)
            zk.start()
        
            assert type(zk).__name__ == 'KazooClient'
        except KazooTimeoutError as error:
            print("{0} check your connection with zookeeper server: {1} ").format(error, srv)

        zk.stop()

        
def test_splitZnodeString():
    '''
    Test for splitZnodeString() parser.
    '''

    testTup = ({"string":"groupname1:hostname1,var1:val1,var2:val2,var3:val3",
                "output":{"groupname1":{"hostname1":{"var1":"val1", "var2":"val2", "var3":"val3"}}}},
               {"string":"kafka:kafka01,fqdn:kafka01.fqdn.com,ipv4:1.2.3.4,kafka-id:1",
                "output":{"kafka":{"kafka01":{"fqdn":"kafka01.fqdn.com","ipv4":"1.2.3.4","kafka-id":"1"}}}},
               {"string":"zoo:zoo-srv01,fqdn:zoo-srv01.fqdn.com,ipv4:2.3.4.5,zoo-id:1",
                "output":{"zoo":{"zoo-srv01":{"fqdn":"zoo-srv01.fqdn.com","ipv4":"2.3.4.5","zoo-id":"1"}}}}
    )

    for varDict in testTup:
        assert splitZnodeString(varDict['string']) == varDict['output']
        
