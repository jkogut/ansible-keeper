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

tst.groupName     = tst.testDict.keys()[0]                     ## ==> 'testgroupname1'
tst.hostName      = tst.testDict[tst.groupName].keys()[0]      ## ==> 'testhostname1' 

tst.varDict       = tst.testDict[tst.groupName][tst.hostName]  ## ==> {'var1': 'val1', 'var3': 'val3', 'var2': 'val2'}
tst.oneDict       = {tst.groupName:{tst.hostName:tst.varDict}} ## ==> {'testgroupname1': {'testhostname1': {'var1': 'val1', 'var3': 'val3', 'var2': 'val2'}}}

tst.hostPath      = "{0}/hosts/{1}".format(cfg.aPath, tst.hostName)
tst.groupPath     = "{0}/groups/{1}".format(cfg.aPath, tst.groupName)
tst.hostGroupPath = "{0}/groups/{1}/{2}".format(cfg.aPath, tst.groupName, tst.hostName)

tst.groupHostStr  = "{0}:{1}".format(tst.groupName, tst.hostName) ## ==> 'testgroupname1:testhostname1'
tst.hostHostStr   = "hosts:{0}".format(tst.hostName)              ## ==> 'hosts:testhostname1'

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

                
    def test_addHostWithHostvars(self, rw_zk):
        '''
        Test if hostname-znode added with addHostWithHostvars(var) exists.
        '''

        ## 1. check if Znode provided with test config exists
        ## 2. run addHostWithHostvars(var) function
        ## 3. check hostname value against tested values (from tst.testDict)
        ## 4. run twice deleteZnodeRecur(var) to remove hostname from groupname and hosts group 
    
        if rw_zk.exists(tst.hostPath) is not None:
            rw_zk.delete(tst.hostPath, recursive=True)
            rw_zk.stop()

        addHostWithHostvars(tst.oneDict)

        try:
            assert rw_zk.exists(tst.hostPath) ## is not None

        finally:
            rw_zk.stop()
            
        deleteZnodeRecur(splitZnodeString(tst.groupHostStr))
        deleteZnodeRecur(splitZnodeString(tst.hostHostStr))

        
    def test_addHostToGroup(self, rw_zk):
        '''
        Test if hostname-znode added with addHostToGroup(var) exists.
        '''

        ## 1. check if Znode provided with test config exists
        ## 2. run addHostWithHostvars(var) and addHostToGroup(var) functions
        ## 3. check if hostname added with addHostToGroup exists
        ## 4. run twice deleteZnodeRecur(var) to remove hostname from groupname and hosts group
    
        if rw_zk.exists(tst.groupPath) is not None:
            rw_zk.delete(tst.groupPath, recursive=True)
            rw_zk.stop()

        addHostWithHostvars(tst.oneDict)
        addHostToGroup(splitZnodeString(tst.groupHostStr))

        try:
            assert rw_zk.exists(tst.hostGroupPath) ## is not None

        finally:
            rw_zk.stop()
            
        deleteZnodeRecur(splitZnodeString(tst.groupHostStr))
        deleteZnodeRecur(splitZnodeString(tst.hostHostStr))

                
    def test_deleteZnodeRecur(self, rw_zk):
        '''
        Test that znode deleted with deleteZnodeRecur(var) does not exist.
        '''

        ## 1. run addHostWithHostvars(var) function to add example Znode provided in test config
        ## 2. run twice deleteZnodeRecur(var) function to delete given Znode provided in test config
        ## 3. check Znode path against that string 

        addHostWithHostvars(tst.oneDict)
        deleteZnodeRecur(splitZnodeString(tst.groupHostStr))
        deleteZnodeRecur(splitZnodeString(tst.hostHostStr))

        try:
            assert rw_zk.exists(tst.hostPath) is None
            assert rw_zk.exists(tst.hostGroupPath) is None

        finally:
            rw_zk.stop()


    def test_deleteZnodeHostExistance(self):
        '''
        Test that deleteZnodeRecur() will inform us that we want to delete nonexistent Znode from hosts group.
        '''

        errStringHost  = 'ERROR  ==> could not delete host: {0} that does not exist !!!'.format(tst.hostName)

        assert deleteZnodeRecur(splitZnodeString(tst.hostHostStr)) == errStringHost


    def test_deleteZnodeHostInGroupExistance(self):
        '''
        Test that deleteZnodeRecur() will inform us that we want to delete nonexistent Znode from groups/groupname group.
        '''

        errStringGroup  = 'ERROR  ==> could not delete host: {0} that does not exist in group: {1} !!!'.format(tst.hostName, tst.groupName)

        addHostWithHostvars(tst.oneDict)
        deleteZnodeRecur(splitZnodeString(tst.groupHostStr))

        assert deleteZnodeRecur(splitZnodeString(tst.groupHostStr)) == errStringGroup

        deleteZnodeRecur(splitZnodeString(tst.hostHostStr))

        
    def test_deleteZnodeRecurGroup(self, rw_zk):
        '''
        Test that znode deleted with deleteZnodeRecur(var) for groupname does not exist.
        '''

        ## 1. run addHostWithHostvars(var) function to create given Znode provided in tst.oneDict 
        ## 2. run deleteZnodeRecur(var) function to delete given Znode provided in tst.groupName
        ## 3. check Znode path against that string
        ## 4. delete hostname Znode in hosts group with deleteZnodeRecur(var)

        addHostWithHostvars(tst.oneDict)
        deleteZnodeRecur(splitZnodeString(tst.groupName))

        try:
            assert rw_zk.exists(tst.groupPath) is None

        finally:
            rw_zk.stop()
            
        deleteZnodeRecur(splitZnodeString(tst.hostHostStr))

        
    def test_hostVarsShowOneHost(self):
        '''
        Test hostVarsShow() function for group with one host.
        '''

        ## 1. run addHostWithHostvars(var) function to create given Znode with vars provided in tst.oneDict 
        ## 2. test showHostVars(var) against vars and values provided in tst.oneDict 
        ## 3. run deleteZnodeRecur(var) function to delete given Znode provided in tst.hostHostStr 

        addHostWithHostvars(tst.oneDict)

        testList = [(tst.hostHostStr,{tst.hostName:tst.varDict}),(tst.groupName, tst.oneDict[tst.groupName])]
    
        for val in testList:
            assert showHostVars(splitZnodeString(val[0])) == val[1]
    
        deleteZnodeRecur(splitZnodeString(tst.groupHostStr))
        deleteZnodeRecur(splitZnodeString(tst.hostHostStr))


    # def test_hostVarsShowMultipleHosts(self):
    #     '''
    #     Test hostVarsShow() function for group with multiple hosts.
    #     '''

    #     ## 1. run addHostWithHostvars(var) function to create given Znode with vars provided in tst.oneDict 
    #     ## 2. test showHostVars(var) against vars and values provided in tst.testDict 
    #     ## 3. run deleteGroupZnode(var) function to delete given Znode provided in tst.hostHostStr 

    #     for hostname in tst.testDict[tst.groupName].keys():
    #         tmpDict = {tst.groupName : { hostname : tst.testDict[tst.groupName][hostname] }}
    #         addHostWithHostvars(tmpDict)

    #     testList = [(tst.hostHostStr, {tst.hostName:tst.varDict}),(tst.groupName, tst.testDict[tst.groupName])]
    
    #     for val in testList:
    #         assert showHostVars(splitZnodeString(val[0])) == val[1]

    #     delete all hosts in group created with addHostWithHostvars(var)    
    #     deleteZnodeRecur(splitZnodeString(tst.groupName))
    #     for hostname in  tst.testDict[tst.groupName].keys():
    #         tmpHostStr = "hosts:{}".format(hostname)
    #         deleteZnodeRecur(splitZnodeString(tmpHostStr))
            
        
    # # def test_updateZnode():
    # #     '''
    # #     Test updated Znode with updateZnode(var).
    # #     '''

    # #     ## 1. run addHostWithHostvars(var) function to create given Znode provided in tst.testDict
    # #     ## 2. run updateZnode(var) function to update given Znode provided in tst.updateDict
    # #     ## 3. check upated results against tst.updateDict
    # #     ## 4. run deleteZnodeRecur(var) function to delete given Znode provided in tst.hostHostStr
    
    # #     addHostWithHostvars(tst.testDict)
    # #     updateZnode(tst.updateDict)

    # #     zk = KazooClient(hosts=cfg.zkServers)
    # #     zk.start()

    # #     for key in tst.updateDict[tst.groupName][tst.hostName].keys():
    # #         zkGet     = zk.get('{0}/{1}'.format(tst.hostGroupPath, key))[0]
    # #         updateValue = tst.updateDict[tst.groupName][tst.hostName][key]
    # #         assert zkGet == testValue

    # #         zk.stop()
            
    # #     deleteZnodeRecur(splitZnodeString(tst.groupName))


class TestSplitters(object):
    '''
    Suite of tests splitter functions 
    '''
    
    def test_splitZnodeString(self):
        '''
        Test for splitZnodeString() parser.
        '''

        testTup = ({"string": tst.groupHostStr,
                    "output": [(tst.groupName, tst.groupPath), (tst.hostName, tst.hostPath, tst.hostGroupPath)]},
                   {"string": tst.hostHostStr,
                    "output": [(tst.hostName, tst.hostPath, None)]},
                   {"string": tst.groupName,
                    "output": [(tst.groupName, tst.groupPath)]}
        )
        
        for znodeStringDict in testTup:
            assert splitZnodeString(znodeStringDict['string']) == znodeStringDict['output']


    def test_splitZnodeVarString(self):
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
