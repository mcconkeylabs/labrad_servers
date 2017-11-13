import subprocess as S
import os, os.path, sys
from time import sleep
from threading import Thread
from PyQt5.QtCore import QObject, pyqtSignal
from labrad.util import runServer
    
MANAGER_FOLDER = r'C:\LabRAD\scalabrad-0.6.3\bin'
MANAGER_SCRIPT = 'labrad.bat'


MGR_SCRIPT = r'C:\local_labrad\scalabrad-0.8.3\bin\labrad.bat'
WEB_SCRIPT = r'C:\local_labrad\scalabrad-web-server-2.0.4\bin\labrad-web.bat'

ENV_VARS = { 'LABRADPASSWORD' : '12345',
             'LABRADREGISTRY' : r'file:///C:/LabRAD/registry.db'}

def labrad_environ():
    for (k, v) in ENV_VARS.iteritems():
        os.environ[k] = v
    return os.environ
    
class ProcessWrapper(QObject):
    
    nameDefault = "Process"
    
    outputAvailable = pyqtSignal('QString') 
     
    def __init__(self, args = [], env = None):
        super(ProcessWrapper, self).__init__()
        self.args = args
        self._set_env(env)
    
    def __del__(self):
        self.stop()
        
    @property
    def name(self):
        return self.nameDefault
        
    def start(self):
        #shell flag ensures batch scripts run
        self.proc = S.Popen(self.args, 
                            env=self.env, 
                            shell = True,
                            stdout = S.PIPE,
                            stderr = S.STDOUT)
        
        self.poller = Thread(target = self._poll_proc)
        self.poller.start()
        
    def stop(self):
        if hasattr(self, 'proc'):
            self.proc.poll()
            if self.proc.returncode is None:
                S.call(['taskkill', '/F', '/T',
                        '/PID', str(self.proc.pid)])
    def running(self):
        '''Returns true if process is running and initialization is complete.
        Override in subclass based on process conditions.
        '''
        return (not hasattr(self, 'proc')) or (self.proc.poll() is not None)
        
    def _poll_proc(self):
         while True:
              ret = self.proc.stdout.readline()
              print '[{}]- {}'.format(self.name, ret)
              
              #process will always kill when other process dies
              #and no output, thread always dies
              if (ret == '') and (self.proc.poll() is not None):
                   return
              else:
                   self.outputAvailable.emit(ret)
                        
    def _set_env(self, env=None):
        self.env = env if env is not None else labrad_environ()

#class NodeWrapper(ProcessWrapper):
#    BASE_ARGS = ['python', '-m', 'labrad.node']
#    
#    def __init__(self, node_name, env=None):
#        self.node_name = node_name
#        self.name = 'Node ' + node_name
#        
#        args = self.BASE_ARGS + ['--name', node_name]
#        super(NodeWrapper, self).__init__(args, env)
#        
#    @property
#    def name(self):
#        return self.name
        
#class ServerWrapper(ProcessWrapper):
#    from twisted.internet import reactor 
#    
#    def __init__(self, serverObject=None, env=None):
#        self.srv = serverObject
#        self._set_env(env)
#        
#    def start(self):
##        runServer(self.srv, False, False)
#        self.thread = Thread(target=self.reactor.run, args=(False,))
#        self.thread.start()
#    
#    def stop(self):
#        self.reactor.stop()
                
            
if __name__ == '__main__':
    scripts = [MGR_SCRIPT] #, WEB_SCRIPT]
    procs = map(lambda x: ProcessWrapper(x), scripts)
    for p in procs:
        p.start()
        
    while True:
        for p in procs:
            line = p.proc.stdout.read()
            if line != '':
                 print line 