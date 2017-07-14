"""
### BEGIN NODE INFO
[info]
name = Spectrum Server
version = 1.0
description = VUV Spectrum Scan Server
instancename = %LABRADNODE% Spectrum Scanner

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 67890124
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from base import BaseScanner

class SpectrumScanner(BaseScanner):
    name = 'Spectrum Server'
    
    