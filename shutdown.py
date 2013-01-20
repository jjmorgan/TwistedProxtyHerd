from twisted.internet import reactor, protocol
import sys

def printUsage():
    print ('Usage: python shutdown.py <server name>\n' +
           '       python shutdown.py all')

class ShutdownClient(protocol.Protocol):
    def connectionMade(self):
        self.transport.write('SHUTDOWN')

def forceShutdown(port):
    factory = protocol.ClientFactory()
    factory.protocol = ShutdownClient
    reactor.connectTCP('127.0.0.1', port, factory)
    reactor.callLater(1.0, reactor.stop)
    reactor.run()

def forceShutdownList(ports):
    factory = protocol.ClientFactory()
    factory.protocol = ShutdownClient
    for p in ports:
        reactor.connectTCP('127.0.0.1', p, factory)
    reactor.callLater(1.0, reactor.stop)
    reactor.run()

if __name__ == '__main__':
    if (len(sys.argv)) != 2:
        printUsage()
        sys.exit()
    if sys.argv[1] == 'all':
        forceShutdownList([12465,12466,12467,12468,12469])
    elif sys.argv[1] == 'blake':
        forceShutdown(12465)
    elif sys.argv[1] == 'bryant':
        forceShutdown(12466)
    elif sys.argv[1] == 'howard':
        forceShutdown(12467)
    elif sys.argv[1] == 'gasol':
        forceShutdown(12468)
    elif sys.argv[1] == 'metta':
        forceShutdown(12469)
    else:
        printUsage()
