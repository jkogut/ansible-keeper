#!/usr/bin/env python

__author__     = "Jan Kogut"
__copyright__  = "Jan Kogut"
__license__    = "MIT"
__version__    = "0.0.1"
__maintainer__ = "Jan Kogut"
__status__     = "Beta"


import json
from optparse import OptionParser
from kazoo.client import KazooClient



## START of config section
##################################################

class OurConfig(object):
    ''' Our config section '''

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
                      help="add hostname with hostvars: <groupname1:newhostname1,var1:value1,var2:value2,var3:value3>")
    parser.add_option("-G", nargs = 1,
                      help="add hostname to hostgroup: <groupname:hostname>")
    parser.add_option("-D", nargs = 1,
                      help="delete hostname or groupname recursively: <groupname1:hostname1> or <groupname1> or <hosts:hostname1>")
    parser.add_option("-U", nargs = 1,
                      help="update hostname with comma separated hostvars: <groupname1:newhostname1,var1:newvalue1,var2:newvalue2>")
    parser.add_option("-S", nargs = 1,
                      help="show hostvars for a given hostname or groupname: <groupname1:newhostname1> or <groupname1>")
    parser.add_option("-I", nargs = 1,
                      help="inventory mode: true|ansible dumps inventory in json format from zookeeper")

    
    (opts, args) = parser.parse_args()
    
    
    if (opts.A or opts.G or opts.D or opts.U or opts.I or opts.S) == None:

        parser.print_help()
        exit(-1)
        
    return {'addMode':opts.A, 'groupMode':opts.G, 'deleteMode':opts.D, 'updateMode':opts.U,
            'showMode':opts.S, 'inventoryMode':opts.I}


def zkStartRo():
    '''
    Start a zookeeper client connection in read-only mode.

    Return zookeeper read-only connection object.
    '''

    zk = KazooClient(hosts=cfg.zkServers, read_only = True)
    zk.start()
    
    return zk


def zkStartRw():
    '''
    Start a zookeeper client connection in read-write mode.

    Return zookeeper read-write connection object.
    '''

    zk = KazooClient(hosts=cfg.zkServers)
    zk.start()
    
    return zk
    

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
    Splits znodeString into groupName, hostName, groupPath, hostPath, hostGroupPath.

    Return list of tuples or list of tuple.
    '''

    ## spliting example string into list of tuples or list of tuple :
    ## example string: groupname:hostname1
    ## example output: [("groupname","/ansible_zk/groups/groupname"),
    ##                  ("hostname1","/ansible_zk/hosts/hostname1","/ansible_zk/groups/groupname/hostname1")]

    if ':' in znodeString:
        groupName      = znodeString.split(':')[0]
        hostName       = znodeString.split(':')[1]
        groupPath      = "{0}/groups/{1}".format(cfg.aPath, groupName)
        hostPath       = "{0}/hosts/{1}".format(cfg.aPath, hostName)
        hostGroupPath  = "{0}/{1}".format(groupPath, hostName)

        return [(groupName, groupPath),(hostName, hostPath, hostGroupPath)]

    else:
        groupName = znodeString
        groupPath = "{0}/groups/{1}".format(cfg.aPath, groupName)

        return [(groupName, groupPath)]


def addHostWithHostvars(znodeDict):
    '''
    Add existing znode to new group.

    Return a string (ADDED    ==> host: <hostname> to group: <groupname>).
    '''

    zk = zkStartRw()
    
    groupName      = znodeDict.keys()[0]
    hostName       = znodeDict[groupName].keys()[0]
    groupPath      = "{0}/groups/{1}".format(cfg.aPath, groupName)
    hostPath       = "{0}/hosts/{1}".format(cfg.aPath, hostName)
    hostGroupPath  = "{0}/{1}".format(groupPath, hostName)

    if zk.exists(hostPath):
        zk.stop()    
        return "ERROR  ==> host: {0} exists !!!".format(hostName, groupName)

    elif zk.exists(hostGroupPath):
        zk.stop()    
        return "ERROR  ==> host: {0} in group {1} exists !!!".format(hostName, groupName)

    else:
        zk.ensure_path(hostPath)
        zk.ensure_path(hostGroupPath)

        for key in znodeDict[groupName][hostName]:
            varPath = "{0}/{1}".format(hostPath, key)
            varVal  = znodeDict[groupName][hostName][key]
            zk.create(varPath, varVal)

        zk.stop()

        return "ADDED   ==> host: {0} to group: {1}".format(hostName, groupName)


def addHostToGroup(znodeStringSplited):
    '''
    Add host to group.

    Return a string (ADDED    ==> host: <hostname> to group: <groupname>).
    '''

    zk = zkStartRw()

    groupName      = znodeStringSplited[0][0]
    groupPath      = znodeStringSplited[0][1]
    hostName       = znodeStringSplited[1][0]
    hostPath       = znodeStringSplited[1][1]
    hostGroupPath  = znodeStringSplited[1][2]

    if zk.exists(hostGroupPath):
        zk.stop()    
        return "ERROR  ==> host: {0} in group {1} exists !!!".format(hostName, groupName)

    if zk.exists(hostPath) is None:
        zk.stop()
        return "ERROR  ==> host: {0} does not exist !!! Could not add non-existent host: {0} to group: {1}".format(hostName, groupName)
        
    zk.ensure_path(hostGroupPath)
    zk.stop()

    return "ADDED   ==> host: {0} to group: {1}".format(hostName, groupName)


def deleteZnodeRecur(znodeStringSplited):
    '''
    Delete znode recursivelly for a given string <groupname> or <hosts:hostname> or <groupname:hostname>.

    Return a string (DELETED||ERROR  ==> [host: <hostname> || group: <groupname>]).
    '''

    zk = zkStartRw()

    if len(znodeStringSplited) > 1:

        groupName      = znodeStringSplited[0][0]
        groupPath      = znodeStringSplited[0][1]
        hostName       = znodeStringSplited[1][0]
        hostPath       = znodeStringSplited[1][1]
        hostGroupPath  = znodeStringSplited[1][2]

        if zk.exists(hostPath) is None:
            zk.stop()   
            return "ERROR  ==> could not delete host: {0} that does not exist !!!".format(hostName)

        if zk.exists(hostGroupPath) is None:
            zk.stop()   
            return "ERROR  ==> could not delete host: {0} that does not exist in group: {1} !!!".format(hostName, groupName)

        ## delete group if there is only one host in it
        if len(zk.get_children(groupPath)) == 1:
            zk.delete(groupPath, recursive=True)

        else:
            zk.delete(hostGroupPath, recursive=True)
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


# def updateZnode(znodeDict):
#     '''
#     Update znode with hostvars.

#     Return a string (UPDATED   ==> host: <hostname> to group: <groupname>).
#     '''
    
#     zk = zkStartRw()
    
#     groupName   = znodeDict.keys()[0]
#     hostName    = znodeDict[groupName].keys()[0]
#     groupPath   = "{0}/groups/{1}".format(cfg.aPath, groupName)
#     hostPath    = "{0}/{1}".format(groupPath, hostName)
#     hostVarList = zk.get_children(hostPath)
    
#     if zk.exists(hostPath) is None:
#         zk.stop()    
#         return "ERROR  ==> host: {0} in group {1} does not exist !!!".format(hostName, groupName)

#     for hostVar in hostVarList:
#         if zk.exists("{0}/{1}".format(hostPath, hostVar)) is None: 
#             zk.stop()            
#             return "ERROR  ==> hostvar: {0} for host {1} in group {2} does not exist !!!".format(hostVar, hostName, groupName)
    
#     for key in znodeDict[groupName][hostName]:
#         varPath = "{0}/{1}".format(hostPath, key)
#         varVal  = znodeDict[groupName][hostName][key]
#         if CONDITION: #FIXME!!!
#            zk.create(varPath, varVal)

#     zk.stop()
#     return "ADDED   ==> host: {0} to group: {1}".format(hostName, groupName)


def hostVarsShow(znodeStringSplited):
    '''
    Show hostvars for a given <groupname:hostname> or <groupname>.
    
    Return dict or string (in case of ERROR).
    '''

    zk = zkStartRo()
    
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

            return valDict

    else:
        return "ERROR with processing znodeStrings !!!"
                    
    zk.stop()
    return valDict


def inventoryDump():
    '''
    Inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Return dict.
    '''

    zk = zkStartRo()

    hostsList  = zk.get_children("{}/hosts".format(cfg.aPath))
    groupsList = zk.get_children("{}/groups".format(cfg.aPath))
    dumpDict   = {"hosts": hostsList}
    
    for group in groupsList:
        path     = "{0}/groups/{1}".format(cfg.aPath, group)
        children = zk.get_children(path)
        dumpDict[group] = children
    
    zk.stop()
    return dumpDict


def ansibleInventoryDump():
    '''
    Ansible compliant inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Return dict.
    '''
    
    zk = zkStartRo()

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
        znodeDict = splitZnodeVarString(oParser()['addMode'])
        print addHostWithHostvars(znodeDict)

    if oParser()['groupMode'] is not None:
        znodeStringSplited = splitZnodeString(oParser()['groupMode'])
        print addHostToGroup(znodeStringSplited)

    if oParser()['deleteMode'] is not None:
        znodeStringSplited = splitZnodeString(oParser()['deleteMode'])
        print deleteZnodeRecur(znodeStringSplited)

    if oParser()['showMode'] is not None:
        znodeStringSplited = splitZnodeString(oParser()['showMode'])
        print json.dumps(hostVarsShow(znodeStringSplited))
                                  
        
if __name__ == "__main__":
    main()
