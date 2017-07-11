from labrad.server import LabradServer, setting, Signal
from twisted.internet.threads import deferToThread
from twisted.internet.defer import returnValue, inlineCallbacks
from time import sleep

class TestServer2(LabradServer):
    
    name = 'Test Server 2'
    ID = 457
    
    @inlineCallbacks
    def initServer(self):
        self.ts = self.client.test_server
        yield self.ts.signal__test_signal(self.ID)
        yield self.ts.addListener(listener = self.testCall,
                                  source = None, ID = self.ID)
        
    def testCall(self, ctx, num):
        print 'Ran %d' % num
    
    @setting(1, 'Test', returns='b')
    def test(self, c):
        print 'Something'
        return False
        
__server__ = TestServer2()        
        
if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)