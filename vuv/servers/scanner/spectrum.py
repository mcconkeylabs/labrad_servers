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

from labrad.server import setting, Signal
from base import BaseScanner

class SpectrumScanner(BaseScanner):
     name = '%LABRADNODE% Spectrum Scanner'
    
     def init_scan(self):
          pass
     
     def scan_pass(self):
          pass
     
     def end_scan(self):
          pass
     
     @setting(1000, 'Beginning', start='v[]', returns='v[]')
     def beginning(self, ctx, start=None):
          pass
     
     @setting(1001, 'End', end='v[]', returns='v[]')
     def end(self, ctx, end=None):
          pass
     
     