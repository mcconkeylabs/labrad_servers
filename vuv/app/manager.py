import subprocess, re, os

ROOT_DIR = r'C:\LabRAD\scalabrad-0.6.3\bin'
LABRAD_EXE = 'labrad.bat'
REGISTRY_URI = 'file:///C:/LabRAD/registry.db'
PASSWORD = ''

ENV_VARS = {'LABRADPASSWORD' : PASSWORD,
            'LABRADREGISTRY' : REGISTRY_URI}
            
#completion regex
OK_STR = r'now accepting labrad connections: port=\d+, tlsPolicy=ON'
REGEX = re.compile(OK_STR)

os.environ['LABRADPASSWORD'] = PASSWORD
os.environ['LABRADREGISTRY'] = REGISTRY_URI

def mgrStart():
    #set environment variables
    for (k, v) in ENV_VARS.iteritems():
        os.environ[k] = v
        
    #go to scalalabrad directory and open manager
    os.chdir(ROOT_DIR)    
    labradProc = subprocess.Popen(LABRAD_EXE, bufsize=1, 
                                  stdout=subprocess.PIPE)
    
    print 'Opening LabRAD Manager...'
    
    #scan manager output looking for bootup completes
    for line in iter(labradProc.stdout.readline, b''):
        print 'LabRAD: %s' % line
        match = REGEX.search(line)
        if match:
            break
    
    print 'LabRAD Manager loading complete...'
    return labradProc
    
def nodeStart(name):
    callStr = 'python -m labrad.node --name %s' % name
    proc = subprocess.Popen(callStr, bufsize = 1, stdout = subprocess.PIPE)
    return proc