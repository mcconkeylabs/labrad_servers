import subprocess as S
import os, os.path, sys
from threading import Thread
from labrad.util import runServer
    
MANAGER_FOLDER = r'C:\LabRAD\scalabrad-0.6.3\bin'
MANAGER_SCRIPT = 'labrad.bat'

ENV_VARS = { 'LABRADPASSWORD' : '12345',
             'LABRADREGISTRY' : r'file:///C:/LabRAD/registry.db'}

def labrad_environ():
    for (k, v) in ENV_VARS.iteritems():
        os.environ[k] = v
    return os.environ
    
class ProcessWrapper(object):
    def __del__(self):
        self.stop()
        
    def stop(self):
        if hasattr(self, 'proc'):
            self.proc.poll()
            if self.proc.returncode is None:
                S.call(['taskkill', '/F', '/T',
                        '/PID', str(self.proc.pid)])

class ManagerWrapper(ProcessWrapper):
    def __init__(self, env=None):
        if env is None:
            env = labrad_environ()
            
        os.chdir(MANAGER_FOLDER)
        self.proc = S.Popen(MANAGER_SCRIPT, env=env)
    
class NodeWrapper(ProcessWrapper):
    def __init__(self, name=None, env=None):
        if env is None:
            env = labrad_environ()
            
        ARGS = ['python', '-m', 'labrad.node']
        if name is not None:
            ARGS = ARGS + ['--name', name]
            
        self.proc = S.Popen(ARGS, env=env)
        
class ServerWrapper(object):
    from twisted.internet import reactor 
    
    def __init__(self, serverObject=None):
        self.srv = serverObject
        
    def start(self):
#        runServer(self.srv, False, False)
        self.thread = Thread(target=self.reactor.run, args=(False,))
        self.thread.start()
    
    def stop(self):
        self.reactor.stop()
        
if __name__ == '__main__':
    mgr = ManagerWrapper()
    node = NodeWrapper()
            
    sys.stdin.readline()