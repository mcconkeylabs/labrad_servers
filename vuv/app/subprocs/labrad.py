import re, shlex
from procs import ProcessWrapper
from vuv import definitions as D

SRV_MSG_RE_STR = r'(?P<stamp>\d+:\d+:\d+\.\d+)\s+\[(?P<origin>\w+)\]\s+(?P<type>\w+)\s+(?P<object>[^\-\s]+) - (?P<message>[^\n]+)\b'
SRV_REGEX = re.compile(SRV_MSG_RE_STR)

MGR_OK_STATUS = 'tlsPolicy=ON'
WEB_OK_STATUS = 'now serving at'

class LabradExecutable(ProcessWrapper):
     ok_message = None
     exe_path = None
     
     def __init__(self):
          super(LabradExecutable, self).__init__(args=[self.exe_path])
          
          self.booted = False
          self.check_regex = re.compile(self.ok_message)
          
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
     ok_message = MGR_OK_STATUS
     exe_path = D.MANAGER_SCRIPT
     
class WebServerProcess(LabradExecutable):
     ok_message = WEB_OK_STATUS
     exe_path = D.WEB_SCRIPT
     
class LabradNodeProcess(ProcessWrapper):
     NODE_CALL = 'python -m labrad.node --name='
     def __init__(self, name):
          #add name to call and then split into arg list before super call
          call = self.NODE_CALL + name
          args = shlex.split(call)
          super(LabradNodeProcess, self).__init__(args=args)
          
          self.booted = False
          self.outputAvailable.connect(self._scan_output)
          
     def running(self):
          if super(LabradNodeProcess, self).running():
               return self.booted
          
     def _scan_output(self, line):
          pass
     