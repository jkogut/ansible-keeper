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

    Return dict (parsed options).
    '''

    parser = OptionParser(usage="usage: %prog [opts] <args>",
                          version="%prog 0.0.1")
    parser.add_option("-A", nargs = 1,
                      help="add host: <groupname:newhost1,var1:value1,var2:value2,var3:value3>")
    parser.add_option("-D", nargs = 1,
                      help="delete hostname or groupname recursively: <groupname:newhost1> or <groupname>")
    parser.add_option("-U", nargs = 1,
                      help="update host with comma separated hostvars")
    parser.add_option("-S", nargs = 1,
                      help="show hostvars for a given hostname or groupname: <groupname:newhost1> or <groupname>")
    parser.add_option("-I", nargs = 1,
                      help="inventory mode: dumps inventory in json format from zookeeper")

    
    (opts, args) = parser.parse_args()
    
    
    if (opts.A or opts.D or opts.U or opts.I or opts.S) == None:

       parser.print_help()
       exit(-1)
        
    return {'addMode':opts.A, 'deleteMode':opts.D, 'updateMode':opts.U,
            'showMode':opts.S, 'inventoryMode':opts.I}


def splitZnodeVarString(znodeVarString):
    '''
    Parse string for commandline opts: <-A|-U>.

    Return dict.
    '''

    ## spliting example string into dictionary:
    ## example string: groupname:hostname1,var1:val1,var2:val2,var3:val3
    ## desired dict  : {"groupname":{"hostname1":{"var1":"val1", "var2":"val2", "var3":"val3"}}}

    varList = znodeVarString.split(',')
    varDict = {}

    for var in varList[1:]:
       varDict[var.split(':')[0]] = var.split(':')[1]
       
    groupName, hostName = varList[0].split(':')[0], varList[0].split(':')[1]

    return { groupName : { hostName : varDict }}


def splitZnodeString(znodeString):
    '''
    Splits znodeString into groupName, hostName, groupPath, hostPath.

    Return list of tuples.
    '''

    ## spliting example string into list of tuples or tuple :
    ## example string: groupname:hostname1
    ## example output: [("groupname","/ansible_zk/groups/groupname"),("hostname1","/ansible_zk/groups/groupname")]

    if ':' in znodeString:
       groupName = znodeString.split(':')[0]
       hostName  = znodeString.split(':')[1]
       groupPath = "{0}/groups/{1}".format(cfg.aPath, groupName)
       hostPath  = "{0}/{1}".format(groupPath, hostName)
       return [(groupName, groupPath),(hostName, hostPath)]

    else:
       groupName = znodeString
       groupPath = "{0}/groups/{1}".format(cfg.aPath, groupName)
       return [(groupName, groupPath)]


def addZnode(znodeDict):
    '''
    Add new znode with hostvars.

    Return a string (ADDED    ==> host: <hostname> to group: <groupname>).
    '''

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    groupName = znodeDict.keys()[0]
    hostName  = znodeDict[groupName].keys()[0]
    groupPath = "{0}/groups/{1}".format(cfg.aPath, groupName)
    hostPath  = "{0}/{1}".format(groupPath, hostName)

    if zk.exists(hostPath):
       zk.stop()    
       return "ERROR  ==> host: {0} in group {1} exist !!!".format(hostName, groupName)
    
    if zk.exists(groupPath):
       zk.create(hostPath)
    else:
       zk.ensure_path(hostPath)

    for key in znodeDict[groupName][hostName]:
       varPath = "{0}/{1}".format(hostPath, key)
       varVal  = znodeDict[groupName][hostName][key]
       zk.create(varPath, varVal)

    zk.stop()
    return "ADDED   ==> host: {0} to group: {1}".format(hostName, groupName)


def deleteZnodeRecur(znodeStringSplited):
    '''
    Delete znode with hostvars for a given list of tuple <groupname:hostname>.

    Return a string (DELETED||ERROR  ==> host: <hostname> in group: <groupname>||group: <groupname>).
    '''

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    if len(znodeStringSplited) > 1:

       groupName = znodeStringSplited[0][0]
       groupPath = znodeStringSplited[0][1]
       hostName  = znodeStringSplited[1][0]
       hostPath  = znodeStringSplited[1][1]

       if zk.exists(hostPath) is None:
          zk.stop()   
          return "ERROR  ==> could not delete host: {0} that does not exist !!!".format(hostName)

       if len(zk.get_children(groupPath)) == 1:
          zk.delete(groupPath, recursive=True)
       else:
          zk.delete(hostPath, recursive=True)

       zk.stop()
       return "DELETED ==> host: {0} in group: {1}".format(hostName, groupName)

    elif len(znodeStringSplited) == 1:

       groupName = znodeStringSplited[0][0]
       groupPath = znodeStringSplited[0][1]
       
       if zk.exists(groupPath) is None:
          zk.stop()
          return "ERROR  ==> could not delete group: {0} that does not exist !!!".format(groupName)

       else:
          zk.delete(groupPath, recursive=True)
    else:
       return "ERROR with processing znodeStrings !!!"           
          
    zk.stop()
    return "DELETED ==> group: {0}".format(groupName)


def hostVarsShow(znodeStringSplited):
    '''
    Show hostvars for a given <groupname:hostname> or <groupname>.
    
    Return dict or string (in case of ERROR).
    '''

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()

    if len(znodeStringSplited) > 1:

       groupName = znodeStringSplited[0][0]
       groupPath = znodeStringSplited[0][1]
       hostName  = znodeStringSplited[1][0]
       hostPath  = znodeStringSplited[1][1]
       
       if zk.exists(hostPath) is None:
          zk.stop()
          return "ERROR  ==> no such hostname: {0} in group {1} !!!".format(hostName, groupName)

       else:
          hostVarList = zk.get_children(hostPath)
          valDict     = {}

          for var in hostVarList:
             valDict[var] = zk.get('{0}/{1}'.format(hostPath, var))[0]
       
    elif len(znodeStringSplited) == 1:
       groupName = znodeStringSplited[0][0]
       groupPath = znodeStringSplited[0][1]

       if zk.exists(groupPath) is None:
          zk.stop()    
          return "ERROR  ==> no such groupname: {0} !!!".format(groupName)

       else:
          hostList = zk.get_children(groupPath)
          valDict  = {}
          
          for host in hostList:
             tmpHostPath    = '{0}/{1}'.format(groupPath, host)
             valDict[host]  = zk.get_children('{0}'.format(tmpHostPath))

          for host in valDict.keys():
             varDict = {}
             for var in valDict[host]:
                tmpHostPath   = '{0}/{1}'.format(groupPath, host)
                varDict[var]  = zk.get('{0}/{1}'.format(tmpHostPath, var))[0]
                valDict[host] = varDict
    else:
       return "ERROR with processing znodeStrings !!!"
                    
    zk.stop()
    return valDict


def inventoryDump():
    '''
    Inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Return dict.
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
    
    Return dict.
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

    if oParser()['addMode'] is not None:
       znodeDict = splitZnodeString(oParser()['addMode'])
       print addZnode(znodeDict)

    if oParser()['deleteMode'] is not None:
       znodeStringSplited = splitZnodeString((oParser()['deleteMode']))
       print deleteZnodeRecur(znodeStringSplited)

    if oParser()['showMode'] is not None:
       znodeStringSplited = splitZnodeString((oParser()['showMode']))
       print json.dumps(hostVarsShow(znodeStringSplited))
                                  
        
if __name__ == "__main__":
   main()
