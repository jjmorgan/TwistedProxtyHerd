import sys
from twisted.internet import reactor, protocol

import extserver
import intserver
import intclient
import proxylog

def initialize(serverName, extPort, intIP, intPort, proxyPortList):
    log = proxylog.ProxyLog(serverName + '.txt', serverName)
    locations = dict()

    intServerFactory = intserver.IntServerFactory(log, locations, serverName)
    intServerFactory.protocol = intserver.IntServer
    
    intClientFactory = intclient.IntClientFactory(log, locations, serverName)
    intClientFactory.protocol = intclient.IntClient

    intServerFactory.setClientFactory(intClientFactory)
    intClientFactory.setServerFactory(intServerFactory)

    extFactory = extserver.ExtServerFactory(log, locations, serverName, 
                                            intServerFactory, 
                                            intClientFactory)
    extFactory.protocol = extserver.ExtServer

    reactor.listenTCP(extPort,extFactory)
    log.writeLine('Listening on port ' + str(extPort) + ' for clients...')

    reactor.listenTCP(intPort,intServerFactory)
    log.writeLine('Awaiting connections from proxy servers on port ' + 
                  str(intPort) + '...')

    for p in proxyPortList:
        #intClientFactory = intclient.IntClientFactory(log, locations, serverName)
        #intClientFactory.protocol = intclient.IntClient
        reactor.connectTCP(intIP, p, intClientFactory)
        log.writeLine('Connecting to proxy server on port ' + str(p) + '...')

    reactor.run()

    # Shutdown
    log.writeLine('Shutting down...\n')
