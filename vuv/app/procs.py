import subprocess as S
import os, os.path, sys
from time import sleep
from threading import Thread
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
    
class ProcessWrapper(object):
    def __init__(self, args, env=None):
        self.args = args
        self._set_env(env)
    
    def __del__(self):
        self.stop()
        
    def start(self):
        #shell flag ensures batch scripts run
        self.proc = S.Popen(self.args, 
                            env=self.env, 
                            shell = True,
                            stdout = S.PIPE,
                            stderr = S.STDOUT)
        
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
        pass
        
                        
    def _set_env(self, env=None):
        self.env = env if env is not None else labrad_environ()

class NodeWrapper(ProcessWrapper):
    BASE_ARGS = ['python', '-m', 'labrad.node']
    
    def __init__(self, name, env=None):
        args = self.BASE_ARGS + ['--name', name]
        super(NodeWrapper, self).__init__(args, env)
        
class ServerWrapper(ProcessWrapper):
    from twisted.internet import reactor 
    
    def __init__(self, serverObject=None, env=None):
        self.srv = serverObject
        self._set_env(env)
        
    def start(self):
#        runServer(self.srv, False, False)
        self.thread = Thread(target=self.reactor.run, args=(False,))
        self.thread.start()
    
    def stop(self):
        self.reactor.stop()
        
class ProcessManager(object):
    def __init__(self):
        self.procs = []
    
    def __del__(self):
        for p in self.procs:
            p.stop()
            
                
            
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