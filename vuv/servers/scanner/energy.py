"""
### BEGIN NODE INFO
[info]
name = Energy Scanner
version = 1.0
description = VUV Energy Scan Server
instancename = %LABRADNODE% Energy Scanner

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 6781234
timeout = 20
### END NODE INFO
"""

from labrad.server import setting
from labrad.errors import Error
import labrad.units as U


from base import BaseScanner
from vuv.servers.ortec.mcsSettings import HARDWARE_BOUNDS

V_MIN, V_MAX = map(lambda x: U.Value(x, 'V'), HARDWARE_BOUNDS['Ramp'])

class EnergyScanner(BaseScanner):
    
    name = '%LABRADNODE% Energy Scanner'
     
     def init_scan(self):
          pass
     
     def scan_pass(self):
          pass
     
     def end_scan(self):
          pass
     
     @setting(1000, 'Voltage Ramp', ramp='(v[V]v[V])', returns='(v[V]v[V])')
     def voltage_ramp(self, ctx, ramp=None):
          if ramp is not None:
               start, end = ramp
               if not EnergyScanner._in_bounds(start):
                    raise Error('Start voltage out of range')
               elif not EnergyScanner._in_bounds(end):
                    raise Error('Ending voltage out of range')
               
               self.ramp = ramp
          
          return self.ramp
          
     @staticmethod
     def _in_bounds(val):
          return val >= V_MIN and val <= V_MAX
          