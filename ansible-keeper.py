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

    Returns a dictionary (parsed options).
    '''

    parser = OptionParser(usage="usage: %prog [opts] <args>",
                          version="%prog 0.0.1")
    parser.add_option("-A", nargs = 1,
                      help="add host: you can provide comma separated hostvars")
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
                                                                    

# def hostVarsShow(name):
#     '''
#     Show hostvars for a given name of host or group.
    
#     Returns a JSON dump.
#     '''

#     zk = KazooClient(hosts=cfg.zkServers, read_only = True)
#     zk.start()

#     groupList = zk.get_children("{}/groups".format(cfg.aPath))
# #    groupDict = {}

#     if name in groupList:
#         pass   
    
#     for group in groupList:
#         path     = "{0}/groups/{1}".format(cfg.aPath,group)
#         children = zk.get_children(path)
#         tmpDict  = {}
#         tmpDict['hosts'] = children
#         tmpDict['vars']  = {"a":"b"}
#         groupDict[group] = tmpDict
    
#     zk.stop()

#     return json.dumps(groupDict)


def inventoryDump():
    '''
    Inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Returns a JSON dump.
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

    return json.dumps(groupDict)


def ansibleInventoryDump():
    '''
    Ansible compliant inventory dump for a given list of zookeeper servers and ansible-keeper path.
    
    Returns a JSON dump.
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

    return json.dumps(groupDict)
        

def main():
    '''
    Main logic
    '''
    
    if oParser()['inventoryMode'] == 'true':
        print inventoryDump()
       
    if oParser()['inventoryMode'] == 'ansible':
        print ansibleInventoryDump()
                   

        
if __name__ == "__main__":
    main()
