from twisted.internet import protocol
import proxylog

class IntClient(protocol.Protocol):
    def connectionMade(self):
        pass

    def connectionLost(self, reason):
        name = self.factory.proxyServers.get(self, '')
        if name:
            del self.factory.proxyServers[self]
            self.factory.log.writeLine('Lost connection to proxy server: ' + name)
        else:
            self.factory.log.writeLine('Lost connection to unnamed proxy server')

    def dataReceived(self, data):
        # Parse received data
        dataParts = data.split()
        pname = self.factory.proxyServers.get(self, '')
        if len(dataParts) > 0:
            command = dataParts[0].rstrip()

            if command == 'NAME':
                name = dataParts[1].rstrip()
                self.factory.proxyServers[self] = name
                self.factory.log.writeLine('Now communicating with ' + name)
                self.transport.write('NAME ' + self.factory.serverName + '\n')

            elif command == 'UPDATE':
                entry = data[7:]
                self.factory.updateLocation(entry, pname)

            else:
                if pname:
                    self.factory.log.writeLine('Proxy server ' + name +
                                               'sent bad command: \n @ ' + data)
                else:
                    self.factory.log.writeLine('Unnamed proxy server ' +
                                               'sent bad command: \n @ ' + data)
        else:
            if pname:
                self.factory.log.writeLine('Proxy server ' + name +
                                           'sent bad data: \n @ ' + data)
            else:
                self.factory.log.writeLine('Unnamed proxy server ' +
                                           'sent bad data: \n @ ' + data)
 
class IntClientFactory(protocol.ReconnectingClientFactory):

    def __init__(self, log, locations, serverName):
        self.log = log
        self.locations = locations
        self.serverName = serverName
        self.proxyServers = dict()

    def setServerFactory(self, fact):
        self.intServerFactory = fact

    def buildProtocol(self, addr):
        self.log.writeLine('Connected to proxy on port ' + str(addr.port) +
                           ': Awaiting name...')
        self.resetDelay()
        p = self.protocol()
        p.factory = self
        return p

    def sendUpdateAll(self, entry, exceptnames=[]):
        count = 0
        for s in self.proxyServers.keys():
            if not (self.proxyServers[s] in exceptnames):
                s.transport.write('UPDATE ' + entry)
                count = count + 1
        return count

    def updateLocation(self, entry, fromname):
        parts = entry.split()
        clientid = parts[2]
        timestamp = parts[4]
        p = self.locations.get(clientid)
        if p:
            if (float(timestamp) <= float(p.split()[4])):
                self.log.writeLine('Redundant location update from ' + fromname +
                                   ', discarded\n @ ' + entry)
                return

        self.locations[clientid] = entry
        self.log.writeLine('Got location update from ' + fromname +
                           '\n @ ' + entry)

        sSent = self.intServerFactory.sendUpdateAll(entry, [fromname])
        cSent = self.sendUpdateAll(entry, [fromname])

        if sSent > 0 and cSent > 0:
            self.log.writeLine('Transmitted update to ' + str(sSent) +
                               ' proxy client(s) and to ' + str(cSent) +
                               ' proxy server(s)')
        elif sSent > 0:
            self.log.writeLine('Transmitted update to ' + str(sSent) + ' proxy client(s)')
        elif cSent > 0:
            self.log.writeLine('Transmitted update to ' + str(cSent) + ' proxy server(s)')
           
