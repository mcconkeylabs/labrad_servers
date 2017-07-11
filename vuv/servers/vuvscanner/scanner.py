# Copyright (C) 2016  Jeffery Dech
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = Scan Server
version = 1.0
description = VUV Scan control

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 7788901234
timeout = 20
### END NODE INFO
    
Server for controlling VUV scans
"""

from time import sleep
import labrad.units as U
from labrad.server import LabradServer, setting, Signal
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue


CH_LIST = ['Start', 'MCSAdv']
REG_PATH = ['', 'Servers', 'Scanner']
ADV_PER_CH = 8.0
MIN_RATIO = 1 / ADV_PER_CH
MAX_PASSES = 10000L

PARAMETER_DEFAULTS = {'Dwell Time' : U.Value(1.0, 's'),
                      'MCS Ratio' : 1.0,
                      'Passes' : 1,
                      'Scan Range' : ((1000, 0), (2000, 0))}
                      
CHMAP_DEFAULT = {'Start' : 1, 'MCSAdv' : 2}

def ratio2dutycycle(ratio):
    inc = int(ratio * ADV_PER_CH)
    doff = inc - 1
    return (1, doff)

class ScanServer(LabradServer):
    name = 'Scan Server'
    ID = 99988
    
    onScanStart = Signal(99875, 'signal: scan started', 'w')
    onScanComplete = Signal(99876, 'signal: scan complete', 'w')
    onPassComplete = Signal(99877, 'signal: pass complete', 'w')

    @inlineCallbacks
    def initServer(self):
        self.reg = self.client.registry
        yield self._loadRegistry()
        
    @inlineCallbacks
    def stopServer(self):
        yield self._updateRegistry()
        
    @inlineCallbacks
    def _loadRegistry(self):
        p = self.reg.packet()
        p.cd(REG_PATH + ['Devices'])
        p.get('Pulser', key='pulser')
        p.get('MCS', key='mcs')
        p.get('Stepper', key='stepper')
        
        p.cd(REG_PATH + ['Settings'])
        for (k, v) in PARAMETER_DEFAULTS.items():
            p.get(k, True, v, key=k)
        p.get('Channels', True, tuple(CHMAP_DEFAULT.iteritems()), key='chs')
        resp = yield p.send()
        
        #setup devices
        pulserSrvName, self.pulserDeviceName = resp['pulser']
        self.pulser = self.client[pulserSrvName]
        yield self.pulser.select_device(self.pulserDeviceName)
        
        self.mcs = self.client[resp['mcs']]
        self.stepper = self.client[resp['stepper']]
        
        #scan settings
        self.params = dict([(k, resp[k]) for k in PARAMETER_DEFAULTS.keys()])
        self.chMap = dict(resp['chs'])
        
        self.reg.addListener(self._loadRegistry)
        self.reg.notify_on_change(self.ID, True)
        
    @inlineCallbacks
    def _updateRegistry(self):
        p = self.reg.packet()
        p.cd(REG_PATH + ['Devices'])
        p.set('Pulser', (self.pulser.name, self.pulserDeviceName))
        p.set('MCS', self.mcs.name)
        p.set('Stepper', self.stepper.name)
        
        p.cd(REG_PATH + ['Settings'])
        for (k,v) in self.params.iteritems():
            p.set(k, v)
        yield p.send()
        
        
    @inlineCallbacks
    def _prepPulser(self):
        p = self.pulser.packet()
        
        #start channel settings
        p.select_channel(self.chMap['Start'])
        p.state(True)
        p.width(U.Value(10, 'us'))
        p.delay(U.Value(0, 's'))
        p.polarity(True)
        p.output(False)
        p.mode('Single')
         
        #mcs advance settings
        p.select_channel(self.chMap['MCSAdv'])
        p.state(True)
        p.width(U.Value(10, 'us'))
        p.delay(U.Value(0, 's'))
        p.polarity(True)
        p.output(False)
        p.mode('DutyCycle', ratio2dutycycle(self.ratio))
        
        #convert dwell time/MCS channel to dwell per advance
        dwell = self.params['Dwell Time'] * ADV_PER_CH / self.params['MCS Ratio']
        
        #configure global pulse settings
        p.select_channel(0)
        p.trigger_period(dwell)
        p.mode('Burst', self._scanSteps())
         
        yield p.send()  

    @inlineCallbacks
    def _prepMCS(self):
        p = self.mcs.packet()
        p.sweeps(self.params['Passes'])
        p.pass_length(self.params['Pass Length'])
        p.acquisition_mode('RepSum')
        p.discriminator_edge('Rising')
        p.discriminator_level(U.Value(1.0, 'V'))
        p.input_impedance(U.Value(50, 'Ohm'))
        p.voltage_ramp([U.Value(0.0, 'V')])
        p.dwell(U.Value(1.0, 'V'))
        p.external_trigger(False)
        yield p.send() 

    @inlineCallbacks
    def _waitForStepper(self):
        state = yield self.stepper.run_state()
        while state:
            sleep(0.5)
            state = yield self.stepper.run_state()
            
    @inlineCallbacks
    def _scanPass(self):
        ch, frac = self.params['Scan Range'][1]
        yield self.stepper.move_to(ch, frac)
        yield self._prepPulser()
        
        p = self.pulser.packet()
        p.signal__pulser_stopped(self.ID)
        p.addListener(self._scanCallback, source = None, ID = self.ID)
        p.pulser.start()
        yield p.send()
    
    @inlineCallbacks
    def _scanCallback(self, ctx, dev_name):
        if dev_name != self.pulserDeviceName:
            returnValue(None)
            
        #remove listener so we don't get callback when reseting stepper
        self.pulser.removeListener(self._scanCallback, ID = self.ID)
        
        #move the stepper to start position
        ch, frac = self.params['Scan Range'][0]
        #moving to befor the channel then going to the positon
        #removes backlash from changing directions
        yield self.stepper.move_to(ch - 1, frac, True)
        yield self._waitForStepper()
        yield self.stepper.move_to(ch, frac, True)
        
        self.currentPass += 1
        if self.currentPass < self.params['Passes']:
            self.onPassComplete(self.currentPass)
            yield self._scanPass()
        else:
            self.onScanComplete(self.currentPass)
    
    @inlineCallbacks
    def _isRunning(self):
        p = self.pulser.packet()
        p.run_state(key='Trig')
        for ch in ['Start', 'MCSAdv']:
            p.select_channel(self.chMap[ch])
            p.state(key=ch)
        resp = yield p.send()
        states = [resp[ch] for ch in ['Trig', 'Start', 'MCSAdv']]
        returnValue(all(states))
        
    def _scanSteps(self):
        ((aC, aF), (bC, bF)) = self.params['Scan Range']
        start = int(aC * ADV_PER_CH + aF)
        stop = int(bC * ADV_PER_CH + bF)
        return stop - start
    
    @setting(100, 'Start')
    def start(self, c):
        running = yield self._isRunning()
        if running:
            raise Error('A scan is currently in progress')
            
        #move stepper into position and wait until complete
        ch, frac = self.params['Scan Range'][0]
        yield self.stepper.move_to(ch, frac, True)
        yield self._waitForStepper()
            
        #now prepare for scan pass
        self.currentPass = 0
        yield self._prepPulser()
        yield self._prepMCS()
        yield self._scanPass()  
        
        self.onScanStart(self.params['Passes'])
    
    @setting(101, 'Stop')
    def stop(self, c):
        running = yield self._isRunning()
        if not running:
            raise Error('Scan is not running')
        
        p = self.pulser.packet()
        p.removeListener(self._scanCallback, ID = self.ID)
        p.stop()
        yield p.send()
        
    @setting(102, 'Run State', 
             returns='(b?): True if running and possible pass number')
    def run_state(self, c):
        state = yield self._isRunning()
        cPass = self.currentPass if state else None
        returnValue((state, cPass))
    
    @setting(110, 'MCS Ratio', ratio=['w','v[]'], returns='v[]')
    def mcs_ratio(self, c, ratio=None):
        if ratio is not None:
            rounded = int(ratio / MIN_RATIO)
            self.params['MCS Ratio'] = rounded * MIN_RATIO
            
        return self.params['MCS Ratio']
            
    @setting(200, 'Scan Range', start='w', startPartial='w',
             stop='w', stopPartial='w', returns = '((ww)(ww))')
    def scan_range(self, c, start=None, startPartial=0, stop=None, stopPartial=0):
        if start is not None:
            if stop is None:
                raise Error('Must provide stop position')
            elif stop < start or ((start == stop) and (startPartial > stopPartial)):
                raise Error('Stop position must be after start')
                
            self.params['Scan Range'] = ((start, startPartial), (stop, stopPartial))
        return self.params['Scan Range']
    
    @setting(201, 'Dwell Time', 
             dwell='v[s] : Dwell time per channel',
             returns='v[s] : Current dwell time')
    def dwell_time(self, c, dwell=None):
        '''Set/query the current dwell time per MCS channel in seconds'''
        if dwell is not None:
            self.params['Dwell Time'] = dwell
        return self.params['Dwell Time']
    
    @setting(202, 'Passes', passes='w', returns='w')
    def passes(self, c, passes=None):
        '''Set/query the number of passes in a given scan.'''
        if passes is not None:
            self.params['Passes'] = passes
        return self.params['Passes']
        
    @setting(300, 'Init Move')
    def init_move(self, c):
        ch, frac = self.params['Scan Range'][0]
        yield self.stepper.move_to(ch, frac, True)
        yield self._waitForStepper()
        
    @setting(301, 'Prep Scan')
    def prep_pulser(self, c):
        yield self._prepPulser()
        yield self._prepMCS()
        
    @setting(302, 'Scan Pass')
    def scan_pass(self, c):
        yield self._scanPass()
    
        
__server__ = ScanServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)