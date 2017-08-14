"""
### BEGIN NODE INFO
[info]
name = Spectrum Scanner
version = 1.0
description = VUV Spectrum Scan Server
instancename = %LABRADNODE% Spectrum Scanner

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 6789234
timeout = 20
### END NODE INFO
"""

from math import floor
from time import sleep

from twisted.internet.defer import inlineCallbacks

from labrad.server import setting, Signal
from base import BaseScanner, MOVE_DWELL

class SpectrumScanner(BaseScanner):
     name = '%LABRADNODE% Spectrum Scanner'
     
     @inlineCallbacks
     def initServer(self):
          yield self._load_reg()
          yield BaseScanner.initServer(self)
    
     @inlineCallbacks
     def init_scan(self):
          yield self.move_stepper(None, self.start)
     
     @inlineCallbacks
     def scan_pass(self):
          steps = (self.end - self.start).toinc()
          step_ratio = int(floor(steps / self.bins)) 
          dcyc = (1, step_ratio - 1)
          
          yield self._mcs_setup()
          yield self._ch_setup(dcyc, True)
          yield self._trigger_setup(self.dwell, steps)
          yield self._pstart_wait()
          
          yield self.move_stepper(None, -(steps + 8))          
          yield self.move_stepper()
          pass
          
     
     def end_scan(self):
          pass
     
     @inlineCallbacks
     def _load_reg(self):
          reg = self.client.registry
          reg_path = []
          
          yield reg.cd(reg_path)
          self.reg_ctx = reg.context() 
          
          p = yield reg.packet(context = self.reg_ctx)
          p.get('start')
          p.get('end')
          resp = yield p.send()
     
          self.start, self.end = resp['start'], resp['end']
          
     @setting(1000, 'Beginning', start='v[]', returns='v[]')
     def beginning(self, ctx, start=None):
          if start is not None:
               self.start = start
          return self.start
     
     @setting(1001, 'End', end='v[]', returns='v[]')
     def end(self, ctx, end=None):
          if end is not None:
               self.end = end
          return self.end
     
     