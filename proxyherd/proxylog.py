import time

class ProxyLog():

    def __init__(self, fileName, proxyName):
        self.fileName = fileName
        self.name = proxyName

    def writeLine(self, line):
        now = time.localtime(time.time())
        f = open(self.fileName,"a")
        f.write('[' + time.strftime("%H:%M:%S") +
                '] (' + self.name + ") " + line.rstrip() + '\n')
        f.close()
        
