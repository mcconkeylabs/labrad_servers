"""
### BEGIN NODE INFO
[info]
name = VUV Scan Server
version = 1.0
description = Control VUV stepper scans

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 6777901234
timeout = 20
### END NODE INFO
    
Server for VUV Stepper
"""

import labrad.units as U
import calc
from time import sleep
from labrad.server import LabradServer, setting, Signal
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue

CH_NAME = ['Advance', 'Direction']
REG_LOC = ['Servers', 'VUV Scanner']

class InvalidPositionError(Error):
    code = 1001
    msg = 'Stepper position is invalid'

class VUVScanServer(LabradServer):
    
    name = 'VUV Scan Server'
    
    @inlineCallbacks
    def initServer(self):
        self._running = False
        pass
    
    @inlineCallbacks
    def stopServer(self):
        pass
    
    @inlineCallbacks
    def serverConnected(self, ID, name):
        pass
    
    def serverDisconnected(self, ID, name):
        pass
    
    def _updateCh(self, name, num):
        if num is not None:
            self.chs[name] = num
            pass
            
        return self.chs[name]
        
    @inlineCallbacks
    def _pulserChannelInitialSetup(self):
        p = self.pulser.packet()
        
        #adv channel
        p.select_channel(self.chs['Advance'])
        p.width(U.Value(1, 'ms'))
        p.delay(U.Value(0, 's'))
        p.polarity(True)
        p.output(False)
        p.mode('Normal')
        
        #direction channel
        p.select_channel(self.chs['Direction'])
        p.width(U.Value(1, 'ms'))
        p.delay(U.Value(0, 's'))
        p.mode('Normal')
        p.output(False)
        
        yield p.send()
        
    @inlineCallbacks
    def _pulserScanSetup(self, steps, forward):
        p = self.pulser.packet()
        p.select_channel(self.chs['Direction'])
        p.polarity(forward)
        
        #trigger channel
        p.select_channel(0)
        p.mode('Burst', steps)
        p.trigger_period(self.period['s'])
        yield p.send()
        
    def _startCallback(self, devName):
        if devName != self.pulserName:
            return
        
        self._running = True
    
    def _stopCallback(self, devName):
        if devName != self.pulserName:
            return
        
        self._running = False
        pass
        
    
    @setting(105, 'Advance Channel', ch='w', returns='w')
    def advance_channel(self, c, ch=None):
        return self._updateCh('Advance', ch)
    
    @setting(106, 'Direction Channel', ch='w', returns='w')
    def direction_channel(self, c, ch=None):
        return self._updateCh('Direction', ch)            
    
    @setting(110, 'Position', posn = '(ww)', returns='(ww)')
    def position(self, c, posn=None):
        if posn is not None:
            if not calc.isValidCh(posn):
                raise InvalidPositionError()
            self.posn = posn
        return self.posn
        
    @setting(200, 'Move To', position='(ww)')
    def move_to(self, c, position=None):
        if position is not None:
            if not calc.isValidCh(position):
                raise InvalidPositionError()
            self.move_posn = position
        return self.move_posn
    
    @setting(201, 'Scan Range', 
             start='(ww)', end='(ww)', 
             returns='((ww)(ww))')
    def scan_range(self, c, start=None, end=None):
        #ensure if there's a scan start there's an end
        if start is not None:
            if end is None:
                raise Error('No scan end position')
                
        #store possible new positions and retrieve
        sPos = self.position(c, start)
        ePos = self.move_to(c, end)
        return (sPos, ePos)
    
    @setting(202, 'Passes', passes='w', returns='w')
    def passes(self, c, passes=None):
        if passes is not None:
            self.passes = passes
        return self.passes
        
    @setting(203, 'Step Period', period='v[s]', returns='v[s]')
    def step_period(self, c, period):
        if period is not None:
            self.period = period
        return self.period
        
    @setting(300, 'Start')
    def start(self, c):
        pass
    
    @setting(301, 'Stop')
    def stop(self, c):
        pass
    
    @setting(302, 'Current Pass', returns='w')
    def current_pass(self, c):
        pass
    
    