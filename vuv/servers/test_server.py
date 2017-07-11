from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet import threads
from time import sleep
import datetime

class TestServer(LabradServer):
    
    name = 'Test Server'
    ID = 456
    testSignal = Signal(123, 'signal: test signal', 'w')
    
    def initServer(self):
        self.reg = self.client.registry

    @inlineCallbacks
    def fn1(self, arg):
        sleep(0.5)
        print arg
        try:
            self.reg.cd('')
            resp = yield self.reg.dir()
            print resp
        except Exception as e:
            print e
#        dl, fl = self.reg.dir()
#        print dl
#        print fl
#        print '%s Dir list' % arg
#        print dl
#        returnValue(fl)
        
    def fn2(self, arg):
        print '%s: the quick one' % arg
     
    @inlineCallbacks
    def fn3(self, arg):
        fl = yield self.fn1(arg)
        sleep(2.5)
        print 'File list'
        print fl
        
    @inlineCallbacks
    def loop_call(self):
        yield self.fn1('Looped')
        for i in range(10):
            sleep(2)
            print 'Loop iteration %d' % i
            
    @inlineCallbacks
    def slow_call(self):
        sleep(5)
        print 'Called after 5s'
        
        p = self.reg.packet()
        p.cd('')
        p.dir()
        resp = yield p.send()
        print resp['dir']
        
    
    @setting(1, 'Test')
    def test(self, c):
#        yield threads.deferToThread(self.loop_call)
#        threads.callMultipleInThread([(self.loop_call, [], {}),
#                                      (self.fn1, ['Call multiple'], {})])
#                           
        @inlineCallbacks           
        def scall():
            sleep(5)
            print 'Called after 5s'
            
            p = self.reg.packet()
            p.cd('')
            p.dir()
            resp = yield p.send()
            print resp['dir']
            returnValue(resp['dir'])
            
        r = yield threads.deferToThread(scall)
        print 'Final result'
        print r
#         val = yield self.test2(c)
#         returnValue(val)
         
    @setting(2, 'Test2', returns='i')
    def test2(self, c):
        return 5
        
        
__server__ = TestServer()        
        
if __name__ == '__main__':
    from labrad import util
    
    try:
        util.runServer(__server__)
    except Exception as e:
        print e