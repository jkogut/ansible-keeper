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

tst.testDict  = {"testgroupname1":
                 {
                  "testhostname1":{"var1":"val1", "var2":"val2", "var3":"val3"},
                  "testhostname2":{"var1":"val1", "var2":"val2", "var3":"val3"},
                  "testhostname3":{"var1":"val1", "var2":"val2", "var3":"val3"}
                 }
}

tst.groupName = tst.testDict.keys()[0]
tst.hostName  = tst.testDict[tst.groupName].keys()[0]
tst.varDict   = tst.testDict[tst.groupName][tst.hostName]
tst.hostPath  = "{0}/groups/{1}/{2}".format(cfg.aPath, tst.groupName, tst.hostName)
tst.groupPath = "{0}/groups/{1}".format(cfg.aPath, tst.groupName)
tst.delString = "{0}:{1}".format(tst.groupName, tst.hostName)

tst.oneDict   = {tst.groupName:{tst.hostName:tst.varDict}}
#################################################
## END of TestVars: global vars for tests 


def test_zookeeperClusterConnection():
    '''
    Test if we can connect to zookeeper cluster servers.
    '''

    ## example server list string 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'
    zk = KazooClient(hosts=cfg.zkServers, read_only = True)
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
            zk = KazooClient(hosts=srv, read_only = True)
            zk.start()
        
            assert type(zk).__name__ == 'KazooClient'
        except KazooTimeoutError as error:
            print("{0} check your connection with zookeeper server: {1} ").format(error, srv)

        zk.stop()

        
def test_addZnode():
    '''
    Test if znode added with addZnode() exists.
    '''

    ## 1. check if Znode provided with tst.groupPath exists
    ## 2. run addZnode() function
    ## 3. check hostname vars values against testes values (from tst.testDict)
    
    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    if zk.exists(tst.groupPath) is not None:
        zk.delete(tst.groupPath, recursive=True)
    zk.stop()

    addZnode(tst.testDict)

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    for key in tst.testDict[tst.groupName][tst.hostName].keys():
        zkGet     = zk.get('{0}/{1}'.format(tst.hostPath, key))[0]
        testValue = tst.testDict[tst.groupName][tst.hostName][key]
        assert zkGet == testValue

    zk.stop()


def test_deleteZnode():
    '''
    Test that znode deleted with deleteZnode() does not exist.
    '''

    ## 1. run deleteZnode(var) function to delete given Znode provided in tst.delString 
    ## 2. check Znode path against that string 
    
    deleteZnode(tst.delString)

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()
    
    assert zk.exists(tst.hostPath) == None
     
    zk.stop()


def test_deleteZnodeExistance():
    '''
    Test that deleteZnode() will inform us that we want to delete nonexistent Znode.
    '''

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    errString = 'ERROR  ==> could not delete host: {} that does not exist !!!'.format(tst.hostName)
    
    assert deleteZnode(tst.delString) == errString
     
    zk.stop()
    
    
def test_deleteGroupZnode():
    '''
    Test that znode deleted with deleteGroupZnode() does not exist.
    '''

    ## 1. run addZnode(var) function to create given Znode provided in tst.testDict 
    ## 2. run deleteGroupZnode(var) function to delete given Znode provided in tst.delString 
    ## 3. check Znode path against that string 

    addZnode(tst.testDict)
    deleteGroupZnode(tst.groupName)

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    assert zk.exists(tst.groupPath) == None
    
    zk.stop()


def test_hostVarsShowOneHost():
    '''
    Test hostVarsShow() function for group with one host.
    '''

    ## 1. run addZnode(var) function to create given Znode with vars provided in tst.testDict 
    ## 2. test hostVarsShow() against vars and values provided in tst.testDict 
    ## 3. run deleteGroupZnode(var) function to delete given Znode provided in tst.delString 

    addZnode(tst.oneDict)

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    testList = [(tst.delString, tst.varDict),(tst.groupName, tst.oneDict[tst.groupName])]
    
    for val in testList:
        assert hostVarsShow(val[0]) == val[1]
    
    zk.stop()
    
    deleteGroupZnode(tst.groupName)

    
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
        
