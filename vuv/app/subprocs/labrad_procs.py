import re, shlex
import labrad
from procs import ProcessWrapper
#from vuv import definitions as D

SRV_MSG_RE_STR = r'(?P<stamp>\d+:\d+:\d+\.\d+)\s+\[(?P<origin>\w+)\]\s+(?P<type>\w+)\s+(?P<object>[^\-\s]+) - (?P<message>[^\n]+)\b'
SRV_REGEX = re.compile(SRV_MSG_RE_STR)

MGR_OK_STATUS = 'tlsPolicy=ON'
WEB_OK_STATUS = 'now serving at'

NODE_MSG_RE_STR = r'(?P<type>\w+):((?P<source>[\w\.]):(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}-\d{4}))? [(?P<args>.*)]\s*(?P<message>.*)'

MGR_PATH = r'C:\local_labrad\labrad_servers\scalabrad-0.8.3\bin\labrad.bat'
WEB_PATH = r'C:\local_labrad\labrad_servers\scalabrad-web-server-2.0.4\bin\labrad-web.bat'

class LabradExecutable(ProcessWrapper):
     ok_message = None
     exe_path = None
     
     def __init__(self):
          super(LabradExecutable, self).__init__(args=[self.exe_path])
          
          self.booted = False
          self.check_regex = re.compile(self.ok_message)
          
          #connect to poll output
          self.outputAvailable.connect(self._check_status)
          
     def running(self):
          if super(LabradExecutable, self).running():
               return self.booted     
     
     def _check_status(self, line):
          match = SRV_REGEX.match(line)
          
          if match:
               msg = match.group('message')
               
               if self.check_regex.search(msg):
                    self.booted = True
          
class ManagerProcess(LabradExecutable):
     nameDefault = 'Manager'
     
     ok_message = MGR_OK_STATUS
#     exe_path = D.MANAGER_SCRIPT
     exe_path = MGR_PATH
     
class WebServerProcess(LabradExecutable):
     nameDefault = 'Web Server'
    
     ok_message = WEB_OK_STATUS
#     exe_path = D.WEB_SCRIPT
     exe_path = WEB_PATH
     
class LabradNodeProcess(ProcessWrapper):
     NODE_CALL = 'python -m labrad.node --name='
     
     def __init__(self, name):
          #add name to call and then split into arg list before super call
          self.node_name = name
          args = shlex.split(self.NODE_CALL + name)
          super(LabradNodeProcess, self).__init__(args=args)
          
          self.cxn = labrad.connect()
          
          p = self.cxn.registry.packet()
          p.cd(['Nodes', name])
          p.get('autostart')
          resp = p.send()
          
          self._start_set = set(resp['get'])
          
          
     def running(self):
          if not super(LabradNodeProcess, self).running():
               return False
          
          servers = set(x for (n, x) in self.cxn.manager.servers())
          return self._start_set.issubset(servers)
      
     def name(self):
          return 'Node ' + self.node_name
          
          