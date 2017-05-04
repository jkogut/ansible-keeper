'''       
Tests for ansibleKeeper
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
from kazoo.exceptions import *


## START of TestVars: global vars for tests 
##################################################

class TestVars(object):
    """ Test vars section """
    pass
            
tst = TestVars()

tst.testDict  = {"testgroupname1":{"testhostname1":{"var1":"val1", "var2":"val2", "var3":"val3"}}}
tst.groupName = tst.testDict.keys()[0]
tst.hostName  = tst.testDict[tst.groupName].keys()[0]

#################################################
## END of TestVars: global vars for tests 


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

        
def test_addZnode():
    '''
    Test if znode added with addZnode() exists.
    '''

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()
    
    addZnode(tst.testDict)
    testHostPath = "{0}/groups/{1}/{2}".format(cfg.aPath, tst.groupName, tst.hostName)
    for key in tst.testDict[tst.groupName][tst.hostName].keys():
        zkGet     = zk.get('{0}/{1}'.format(testHostPath,key))[0]
        testValue = tst.testDict[tst.groupName][tst.hostName][key]
        assert zkGet == testValue

    zk.stop()


def test_deleteZnode():
    '''
    Test if znode added with addZnode() exists.
    '''

    testString = "testgroupname1:testhostname1"

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()
    
    deleteZnode(testString)
    testHostPath = "{0}/groups/testgroupname1/testhostname1".format(cfg.aPath)
    
    assert zk.exists(testHostPath) == None
    
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
        
