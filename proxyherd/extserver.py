from twisted.internet import reactor, protocol
from twisted.web.client import getPage
import time
import proxylog

def formatIP(client):
    addr = client.transport.getPeer()
    return str(addr.host) + ':' + str(addr.port)

class ExtServer(protocol.Protocol):
    
    def connectionMade(self):
        addr = self.transport.getPeer()
        self.factory.log.writeLine('Connection made: New ' + str(addr.type) + 
                                   ' client from ' + formatIP(self))

    def connectionLost(self, reason):
        self.factory.log.writeLine('Disconnected: Client from ' + formatIP(self))
        
    def dataReceived(self, data):
        # Parse incoming data
        dataParts = data.split()
        if len(dataParts) > 0:
            command = dataParts[0].rstrip()

            if command == 'IAMAT': # Location update
                msg = self.factory.handleIamat(data, dataParts, self)
                self.transport.write(msg)
                if (msg.split()[0]) == 'AT':
                    self.factory.log.writeLine('Sent AT response to ' +
                                     formatIP(self) + '\n > ' + msg)

            elif command == 'WHATSAT': # Twitter request
                self.factory.handleWhatsat(data, dataParts, self)

            else:
                self.transport.write('? ' + data) # Bad command
                self.factory.log.writeLine('Bad command from client ' +
                                 formatIP(self) + '\n < ' + data)
        else:
            self.transport.write('? ' + data) # Empty message
            self.factory.log.writeLine('Bad (empty) request from client ' +
                             formatIP(self) + '\n < ' + data)

class ExtServerFactory(protocol.ServerFactory):

    def __init__(self, log, locations, serverName, intSFact, intCFact):
        self.log = log
        self.locations = locations
        self.serverName = serverName
        self.intServerFactory = intSFact
        self.intClientFactory = intCFact

    def handleIamat(self, data, dataParts, client):
        if (len(dataParts)) != 4:
            self.log.writeLine('Bad IAMAT message from client ' + formatIP(client) +
                               '\n < ' + data)
            return '? ' + data
        clientid = dataParts[1]
        position = dataParts[2]
        timestamp = dataParts[3].rstrip()

        try:  
            # Timestamp difference
            ctime = time.time()
            mytimestamp = '%.09f' % ctime
            timediff = ctime - float(timestamp)
            
            if (position[0] != '+') and (position[0] != '-'):
                raise ValueError('Invalid coordinates')
            pos = position.find('+',1)
            if pos < 0:
                pos = position.find('-',1)
                if pos < 0:
                    raise ValueError('Invalid coordinates')

            # Check integrity of coordinates
            coordx = float(position[0:pos])
            coordy = float(position[pos:])

            # Check for existing entry
            p = self.locations.get(clientid)
            if p:
                if (float(timestamp) <= float(p.split()[4])):
                    # More recent entry is already stored;
                    #   return existing entry
                    return 'AT ' + p 

            # Store and propagate to other proxy servers
            entry = (self.serverName + ' ' + '{0:+0.09f}'.format(timediff)
                    + ' ' + clientid + ' ' + position + ' ' + timestamp + '\n')
            self.locations[clientid] = entry
            
            self.log.writeLine('Got IAMAT update from client ' + formatIP(client) +
                               '\n < ' + data) 

            sSent = self.intServerFactory.sendUpdateAll(entry)
            cSent = self.intClientFactory.sendUpdateAll(entry)

            if sSent > 0 and cSent > 0:
                self.log.writeLine('Sent update to ' + str(sSent) + 
                                   ' proxy client(s) and to ' + str(cSent) +
                                   ' proxy server(s)')
            elif sSent > 0:
                self.log.writeLine('Sent update to ' + str(sSent) + ' proxy client(s)')
            elif cSent > 0:
                self.log.writeLine('Sent update to ' + str(cSent) + ' proxy server(s)')
               
            return 'AT ' + entry
 
        except ValueError:
            self.log.writeLine('Bad IAMAT message from client ' + formatIP(client) +
                               '\n < ' + data) 
            return '? ' + data

    def handleWhatsat(self, data, dataParts, client):
        if (len(dataParts)) != 4:
            client.transport.write('? ' + data)
            self.log.writeLine('Bad WHATSAT message from client ' +
                               formatIP(client) + '\n < ' + data)
            return
        clientid = dataParts[1]
        radius = dataParts[2]
        numtweets = dataParts[3].rstrip()

        try:
           p = self.locations.get(clientid)
           if p:
               pparts = p.split()
               position = pparts[3]
               rad = int(radius) # Throws exception when not valid
               ntweets = int(numtweets) # " "
 
               pos = position.find('+',1)
               if pos < 0:
                   pos = position.find('-',1)

               coordx = float(position[0:pos])
               coordy = float(position[pos:])
               
               # Perform lookup
               self.log.writeLine('Got WHATSAT request from ' + formatIP(client) + 
                                  ' -- Retrieving tweets...' +
                                  '\n' + ' < ' + data)
               geocode = (str(coordx) + ',' + str(coordy) + ',' + str(rad) + 'km')
               rpp = str(ntweets)
               page = ('http://search.twitter.com/search.json?q=&geocode=' +
                       geocode + '&rpp=' + rpp)
               getPage(page).addCallbacks(
                   callback = lambda value:(self.gotTweets(value, client, p)),
                   errback = lambda error:(self.pageError(error))
               )

           else:
               # Location not found
               client.transport.write('NOTFOUND ' + clientid + '\n')
               self.log.writeLine('Client ' + formatIP(client) +
                                  ' requested nonexistent WHATSAT client ID: ' + 
                                  clientid + '\n < ' + data)
               return
              
        except ValueError:
            client.transport.write('? ' + data)
            self.log.writeLine('Bad WHATSAT message from client ' +
                               formatIP(client) + '\n < ' + data)

    def gotTweets(self, value, client, entry):
        client.transport.write('AT ' + entry + value + '\n')
        self.log.writeLine('Search complete. Sent tweets to client: ' + 
                           formatIP(client) + '\n > ' + 'AT ' + entry)

    def pageError(self, error):
        client.transport.write('ERROR ' + error)
        self.log.writeLine('Error sending Twitter search request: ' + error)
        
