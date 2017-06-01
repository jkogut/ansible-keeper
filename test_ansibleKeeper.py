'''       
Tests for ansibleKeeper
'''

__author__     = "Jan Kogut"
__copyright__  = "Jan Kogut"
__license__    = "MIT"
__version__    = "0.0.1"
__maintainer__ = "Jan Kogut"
__status__     = "Beta"


import pytest
import socket
from ansibleKeeper import *
from kazoo.client import KazooClient
from kazoo.handlers.threading import *
from kazoo.exceptions import *


## START of TestVars: global vars for tests 
##################################################

class TestVars(object):
    ''' Test vars section '''
    pass
            
tst = TestVars()

tst.testDict  = {"testgroupname1":
                 {
                  "testhostname1":{"var1":"val1", "var2":"val2", "var3":"val3"},
                  "testhostname2":{"var1":"val11", "var2":"val22", "var3":"val33"},
                  "testhostname3":{"var1":"val111", "var2":"val222", "var3":"val333"}
                 }
}


tst.updateDict  = {"testgroupname1":
                 {
                  "testhostname1":{"var1":"valUpdated1", "var2":"valUpdated2", "var3":"valUpdated3"},
                  "testhostname2":{"var1":"valUpdated11", "var2":"valUpdated22", "var3":"valUpdated33"},
                  "testhostname3":{"var1":"valUpdated111", "var2":"valUpdated222", "var3":"valUpdated333"}
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


class TestConfig(object):
    '''
    Suite of config tests with read-only zookeeper client connection.
    '''

    def test_zkClusterUp(self):
        '''
        Test if the zookeeper cluster is UP.
        We expect all servers are UP and port for zookeeper: 2181 is open. 
        '''

        zkSrvList = cfg.zkServers.replace(':2181','').split(',')

        for srv in zkSrvList:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                assert sock.connect_ex((srv,2181)) == 0

            finally:
                sock.close()
    
    
    @pytest.fixture
    def ro_zk(self):
        '''
        Fixture for zookeeper client connection in read-only mode. 
        '''

        ## example server list string 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'    
        zk = KazooClient(hosts=cfg.zkServers, read_only = True)
        zk.start()
        
        return zk

               
    def test_configZkClusterConnection(self, ro_zk):
        '''
        Test if we can establish zookeeper client connection to zookeeper cluster servers.
        We expect at least one server runnig zookeeper.
        '''

        try:
            assert type(ro_zk).__name__ == 'KazooClient'

        finally:
            ro_zk.stop()

    
    def test_configZkServerConnection(self, ro_zk):
        '''
        Test if we can establish zookeeper client connection to each zookeeper server.
        We expect all of the servers are running zookeeper. 
        '''

        ## example server list string 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'
        zkSrvList = cfg.zkServers.split(',')
    
        for srv in zkSrvList:
            try:
                assert type(ro_zk).__name__ == 'KazooClient'

            except KazooTimeoutError as error:
                print("{0} check your connection with zookeeper server: {1} ").format(error, srv)

            finally:
                ro_zk.stop()

                
    def test_configBasePrefixZnode(self, ro_zk):
        '''
        Test if base prefix znode from config exists.
        '''

        try:
            assert ro_zk.exists(cfg.aPath) is not None

        finally:
            ro_zk.stop()

            
            
class TestReadWrite(object):
    '''
    Suite of tests where read-write zookeeper client connection is required.
    '''

    @pytest.fixture
    def rw_zk(self):
        '''
        Fixture for zookeeper client connection in read-write mode. 
        '''

        ## example server list string 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'    
        zk = KazooClient(hosts=cfg.zkServers)
        zk.start()
        
        return zk

                
    def test_addZnode(self, rw_zk):
        '''
        Test if hostname-znode added with addZnode(var) exists.
        '''

        ## 1. check if Znode provided with test config exists
        ## 2. run addZnode(var) function
        ## 3. check hostname value against testes values (from tst.testDict)
        ## 4. run deleteZnodeRecur(var) 
    
        if rw_zk.exists(tst.groupPath) is not None:
            rw_zk.delete(tst.groupPath, recursive=True)
            rw_zk.stop()

        addZnode(tst.testDict)

        try:
            assert rw_zk.exists(tst.hostPath) is not None

        finally:
            rw_zk.stop()
            
        deleteZnodeRecur(splitZnodeString(tst.delString))

        
    # def test_addZnodeVar(self, rw_zk):
    #     '''
    #     Test if var-znode added with addZnode(var) exists.
    #     '''

    #     ## 1. check if Znode provided with tst.groupPath exists
    #     ## 2. run addZnode(var) function
    #     ## 3. check hostname vars values against testes values (from tst.testDict)
    
    #     if rw_zk.exists(tst.groupPath) is not None:
    #         rw_zk.delete(tst.groupPath, recursive=True)
    #         rw_zk.stop()

    #     addZnode(tst.testDict)

    #     for key in tst.testDict[tst.groupName][tst.hostName].keys():
    #         rw_zkGet     = rw_zk.get('{0}/{1}'.format(tst.hostPath, key))[0]
    #         testValue    = tst.testDict[tst.groupName][tst.hostName][key]

    #         try:
    #             assert rw_zkGet == testValue

    #         finally:
    #             rw_zk.stop()
        
    
    def test_deleteZnodeRecur(self, rw_zk):
        '''
        Test that znode deleted with deleteZnodeRecur(var) does not exist.
        '''

        ## 1. run addZnode(var) function to add example Znode provided in test config
        ## 2. run deleteZnodeRecur(var) function to delete given Znode provided in test config
        ## 3. check Znode path against that string 

        addZnode(tst.testDict)
        deleteZnodeRecur(splitZnodeString(tst.delString))

        try:
            assert rw_zk.exists(tst.hostPath) is None

        finally:
            rw_zk.stop()


    def test_deleteZnodeExistance(self):
        '''
        Test that deleteZnode() will inform us that we want to delete nonexistent Znode.
        '''

        errString = 'ERROR  ==> could not delete host: {} that does not exist !!!'.format(tst.hostName)

        assert deleteZnodeRecur(splitZnodeString(tst.delString)) == errString
    
    
    def test_deleteZnodeRecurGroup(self, rw_zk):
        '''
        Test that znode deleted with deleteZnodeRecur(var) for groupname does not exist.
        '''

        ## 1. run addZnode(var) function to create given Znode provided in tst.testDict 
        ## 2. run deleteZnodeRecur(var) function to delete given Znode provided in tst.delString 
        ## 3. check Znode path against that string 

        addZnode(tst.testDict)
        deleteZnodeRecur(splitZnodeString(tst.groupName))

        try:
            assert rw_zk.exists(tst.groupPath) is None

        finally:
            rw_zk.stop()


    def test_hostVarsShowOneHost(self):
        '''
        Test hostVarsShow() function for group with one host.
        '''

        ## 1. run addZnode(var) function to create given Znode with vars provided in tst.oneDict 
        ## 2. test hostVarsShow() against vars and values provided in tst.testDict 
        ## 3. run deleteZnodeRecur(var) function to delete given Znode provided in tst.delString 

        addZnode(tst.oneDict)

        testList = [(tst.delString, tst.varDict),(tst.groupName, tst.oneDict[tst.groupName])]
    
        for val in testList:
            assert hostVarsShow(splitZnodeString(val[0])) == val[1]
    
        deleteZnodeRecur(splitZnodeString(tst.groupName))


    def test_hostVarsShowMultipleHosts(self):
        '''
        Test hostVarsShow() function for group with multiple hosts.
        '''

        ## 1. run addZnode(var) function to create given Znode with vars provided in tst.testDict 
        ## 2. test hostVarsShow() against vars and values provided in tst.testDict 
        ## 3. run deleteGroupZnode(var) function to delete given Znode provided in tst.delString 

        for key in tst.testDict[tst.groupName].keys():
            tmpDict = {tst.groupName : { key : tst.testDict[tst.groupName][key] }}
            addZnode(tmpDict)

        testList = [(tst.delString, tst.varDict),(tst.groupName, tst.testDict[tst.groupName])]
    
        for val in testList:
            assert hostVarsShow(splitZnodeString(val[0])) == val[1]
    
        deleteZnodeRecur(splitZnodeString(tst.groupName))

        
    # def test_updateZnode():
    #     '''
    #     Test updated Znode with updateZnode(var).
    #     '''

    #     ## 1. run addZnode(var) function to create given Znode provided in tst.testDict
    #     ## 2. run updateZnode(var) function to update given Znode provided in tst.updateDict
    #     ## 3. check upated results against tst.updateDict
    #     ## 4. run deleteZnodeRecur(var) function to delete given Znode provided in tst.delString
    
    #     addZnode(tst.testDict)
    #     updateZnode(tst.updateDict)

    #     zk = KazooClient(hosts=cfg.zkServers)
    #     zk.start()

    #     for key in tst.updateDict[tst.groupName][tst.hostName].keys():
    #         zkGet     = zk.get('{0}/{1}'.format(tst.hostPath, key))[0]
    #         updateValue = tst.updateDict[tst.groupName][tst.hostName][key]
    #         assert zkGet == testValue

    #         zk.stop()
            
    #     deleteZnodeRecur(splitZnodeString(tst.groupName))

        

def test_splitZnodeString():
    '''
    Test for splitZnodeString() parser.
    '''

    testTup = ({"string": "{0}:{1}".format(tst.groupName, tst.hostName),
                "output": [(tst.groupName, tst.groupPath), (tst.hostName, tst.hostPath)]},
               {"string": tst.groupName,
                "output": [(tst.groupName, tst.groupPath)]}
    )

    for znodeStrgingDict in testTup:
        assert splitZnodeString(znodeStrgingDict['string']) == znodeStrgingDict['output']


def test_splitZnodeVarString():
    '''
    Test for splitZnodeVarString() parser.
    '''

    testTup = ({"string":"groupname1:hostname1,var1:val1,var2:val2,var3:val3",
                "output":{"groupname1":{"hostname1":{"var1":"val1", "var2":"val2", "var3":"val3"}}}},
               {"string":"kafka:kafka01,fqdn:kafka01.fqdn.com,ipv4:1.2.3.4,kafka-id:1",
                "output":{"kafka":{"kafka01":{"fqdn":"kafka01.fqdn.com","ipv4":"1.2.3.4","kafka-id":"1"}}}},
               {"string":"zoo:zoo-srv01,fqdn:zoo-srv01.fqdn.com,ipv4:2.3.4.5,zoo-id:1",
                "output":{"zoo":{"zoo-srv01":{"fqdn":"zoo-srv01.fqdn.com","ipv4":"2.3.4.5","zoo-id":"1"}}}}
    )

    for varDict in testTup:
        assert splitZnodeVarString(varDict['string']) == varDict['output']
        
