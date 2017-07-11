import os, re
import labrad
from time import sleep
from subprocess import PIPE, Popen

ROOT_DIR = r'C:\LabRAD\scalabrad-0.6.3\bin'
LABRAD_EXE = 'labrad.bat'
REGISTRY_URI = 'file:///C:/LabRAD/registry.db'
PASSWORD = ''

MANAGER_ARGS = [LABRAD_EXE,
            '--password', PASSWORD,
            '--registry', REGISTRY_URI]
            
OK_STR = r'now accepting labrad connections: port=\d+, tlsPolicy=ON'
REGEX = re.compile(OK_STR)

NODE_ARGS = ['python', 
             '-m', 'labrad.node',
             '--name', 'VUV']

def labradManagerStart():
    #go to scalalabrad directory and open manager
    os.chdir(ROOT_DIR)    
    labradProc = Popen(MANAGER_ARGS, bufsize=1, stdout=PIPE)
    
    print 'Opening LabRAD Manager...'
    
    #scan manager output looking for bootup completes
    for line in iter(labradProc.stdout.readline, b''):
        print 'LabRAD: %s' % line
        match = REGEX.search(line)
        if match:
            break
        
    print 'LabRAD Manager loading complete...'
    return labradProc
    
def nodeStart():
    proc = Popen(NODE_ARGS)
    return proc
    
def startup():
    manager = labradManagerStart()
    node = nodeStart()    
    procs = [manager, node]

    cxn = labrad.connect()
    #wait for vuv stepper server
    while 'vuv_stepper_server' not in cxn.servers:
        sleep(1)
    
    
    
if __name__ == '__main__':
    proc = labradManagerStart()
    proc.terminate()