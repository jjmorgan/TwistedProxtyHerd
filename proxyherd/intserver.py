from twisted.internet import reactor, protocol
import proxylog

class IntServer(protocol.Protocol):
    def connectionMade(self):
        self.factory.log.writeLine('Connection from proxy: Retrieving name...')
        self.transport.write('NAME ' + self.factory.serverName + '\n')

    def connectionLost(self, reason):
        name = self.factory.proxyClients.get(self, '')
        if name:
            del self.factory.proxyClients[self]
            self.factory.log.writeLine('Lost connection from proxy client: ' 
                                       + name)
        else:
            self.factory.log.writeLine('Lost connection from unnamed ' + 
                                       'proxy client')

    def dataReceived(self, data):
        # Parse incoming data
        dataParts = data.split()
        pname = self.factory.proxyClients.get(self, '')
        if len(dataParts) > 0:
            command = dataParts[0].rstrip()

            if command == 'NAME':
                name = dataParts[1].rstrip()
                self.factory.proxyClients[self] = name
                self.factory.log.writeLine('Now communicating with ' + name)

            elif command == 'UPDATE':
                entry = data[7:]
                self.factory.updateLocation(entry, pname)

            elif command == 'SHUTDOWN':
                self.factory.log.writeLine('Shutdown request from proxy')
                for c in self.factory.proxyClients:
                    c.transport.loseConnection()
                reactor.stop()
              
            else:
                if pname:
                    self.factory.log.writeLine('Proxy client ' + name +
                                               'sent bad command: \n @ ' + data)
                else:
                    self.factory.log.writeLine('Unnamed proxy client ' +
                                               'sent bad command: \n @ ' + data)
        else:
            if pname:
                self.factory.log.writeLine('Proxy client ' + name +
                                           'sent bad data: \n @ ' + data)
            else:
                self.factory.log.writeLine('Unnamed proxy client ' +
                                           'sent bad data: \n @ ' + data)

class IntServerFactory(protocol.ServerFactory):

    def __init__(self, log, locations, serverName): 
        self.log = log
        self.locations = locations
        self.serverName = serverName
        self.proxyClients = dict()

    def setClientFactory(self, fact):
        self.intClientFactory = fact

    def sendUpdateAll(self, entry, exceptnames=[]):
        count = 0
        for s in self.proxyClients.keys():
            if not (self.proxyClients[s] in exceptnames):
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

        sSent = self.sendUpdateAll(entry, [fromname])
        cSent = self.intClientFactory.sendUpdateAll(entry, [fromname])

        if sSent > 0 and cSent > 0:
            self.log.writeLine('Transmitted updated to ' + str(sSent) +
                               ' proxy client(s) and to ' + str(cSent) +
                               ' proxy server(s)')
        elif sSent > 0:
            self.log.writeLine('Transmitted update to ' + str(sSent) + ' proxy client(s)')
        elif cSent > 0:
            self.log.writeLine('Transmitted update to ' + str(cSent) + ' proxy server(s)')
