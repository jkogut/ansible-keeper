#!/usr/bin/env python

__author__ = "Jan Kogut"
__copyright__ = "Jan Kogut"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Jan Kogut"
__status__ = "Beta"


import json
from optparse import OptionParser
from kazoo.client import KazooClient



## START of config section
##################################################

class OurConfig(object):
       """ Our config section """
       pass

cfg = OurConfig()

cfg.zkServers  = 'zoo1.dmz:2181,zoo2.dmz:2181,zoo3.dmz:2181'
cfg.aPath      = '/ansible-test'

#################################################
## END of config section 


def oParser():
    '''
    Commandline options parsing function.

    Returns dict (parsed options).
    '''

    parser = OptionParser(usage="usage: %prog [opts] <args>",
                          version="%prog 0.0.1")
    parser.add_option("-A", nargs = 1,
                      help="add host: newhost,var1:value1,var2:value2,var3:value3")
    parser.add_option("-D", nargs = 1,
                      help="delete host and its hostvars")
    parser.add_option("-U", nargs = 1,
                      help="update host with comma separated hostvars")
    parser.add_option("-S", nargs = 1,
                      help="show hostvars for a given hostname or groupname")
    parser.add_option("-I", nargs = 1,
                      help="inventory mode: dumps inventory in json format from zookeeper")

    
    (opts, args) = parser.parse_args()
    
    
    if (opts.A or opts.D or opts.U or opts.I or opts.S) == None:

       parser.print_help()
       exit(-1)
        
    return {'addMode':opts.A, 'deleteMode':opts.D, 'updateMode':opts.U, 'showMode':opts.S, 'inventoryMode':opts.I}


def splitZnodeString(znodeString):
    '''
    Znode string parser.

    Returns dict.
    '''

    ## spliting example string into dictionary:
    ## example string: groupname-hostname,var1:val1,var2:val2,var3:val3
    ## desired dict  : {"groupname":{"hostname":{"var1":"val1", "var2":"val2", "var3":"val3"}}}

    varList = znodeString.split(',')
    varDict = {}

    for var in varList[1:]:
       varDict[var.split(':')[0]] = var.split(':')[1]
       
    groupName, hostName = varList[0].split('-')[0], varList[0].split('-')[1]
    return { groupName : { hostName : varDict }}


# def addZnode(znodeDict):
#     '''
#     Adds new znode with hostvars.
#     '''

#     zk = KazooClient(hosts=cfg.zkServers)
#     zk.start()

#     hostName = znodeDict.keys()[0]
#     hostPath = "{0}/groups/{1}".format(cfg.aPath, hostName)
#     # print hostPath
#     zk.create(hostPath)

#     tmpDict = znodeDict[znodeDict.keys()[0]]

#     for key in tmpDict:
#        varPath = "{0}/groups/{1}/{2}".format(cfg.aPath, hostName,  key)
#        varVal  = tmpDict[key]
#        zk.create(varPath, varVal)
#     zk.stop()

    
def hostVarsShow(name, dumpDict):
    '''
    Show hostvars for a given name of host or group.
    
    Returns JSON dump.
    '''

    if name in tmpDict.keys():
       for host in tmpDict[name]['hosts']:
          print host  
           
    else:
       pass
 

def inventoryDump():
    '''
    Inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Returns dict.
    '''

    zk = KazooClient(hosts=cfg.zkServers, read_only = True)
    zk.start()

    groupList = zk.get_children("{}/groups".format(cfg.aPath))
    groupDict = {}
    
    for group in groupList:
       path     = "{0}/groups/{1}".format(cfg.aPath, group)
       children = zk.get_children(path)
       groupDict[group] = children
    
    zk.stop()

    return groupDict


def ansibleInventoryDump():
    '''
    Ansible compliant inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Returns dict.
    '''

    zk = KazooClient(hosts=cfg.zkServers, read_only = True)
    zk.start()

    groupList = zk.get_children("{}/groups".format(cfg.aPath))
    groupDict = {}
    
    for group in groupList:
       path     = "{0}/groups/{1}".format(cfg.aPath, group)
       children = zk.get_children(path)
       tmpDict  = {}
       tmpDict['hosts'] = children
       tmpDict['vars']  = {"a":"b"}
       groupDict[group] = tmpDict
    
    zk.stop()

    return groupDict
        

def main():
    '''
    Main logic
    '''
    
    if oParser()['inventoryMode'] == 'true':
       print json.dumps(inventoryDump())
       
    if oParser()['inventoryMode'] == 'ansible':
       print json.dumps(ansibleInventoryDump())

    if type(oParser()['addMode']) != 'NoneType':
       znodeDict = splitZnodeString(oParser()['addMode'])
       addZnode(znodeDict)
                                  
        
if __name__ == "__main__":
   main()
