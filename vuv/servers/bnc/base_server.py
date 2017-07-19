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

import time
from labrad.devices import DeviceServer
from labrad.server import Signal, setting
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import threads
    
class NoChannelSelectedError(Error):
    '''No channel selected in the current context.'''
    code = 1007
    
class InvalidChannelError(Error):
    '''No such channel exists for current device.'''
    code = 1008

class BNCBaseServer(DeviceServer):
    name = 'Base BNC Server'
    ID = 67543    
    
    def initServer(self):
        self._killed = False
        DeviceServer.initServer(self)
    
    def selectedChannel(self, ctx):
        #returns channel selected in current context
        try:
            ch = ctx['Channel']
            return ch
        except Exception, e:
            raise NoChannelSelectedError()
            
    def _sdc(self, ctx):
        dev = self.selectedDevice(ctx)
        ch = self.selectedChannel(ctx)
        return (dev,ch)
        
    @inlineCallbacks
    def _monitorPulser(self, device):
        #poll until run end
        state = yield device.run_state()
        while state:
            time.sleep(0.25)
            state = yield device.run_state()
            
        #signal stop
        self.pulserStopped(device.name)
        
    ##### SIGNALS #####
    pulserStarted = Signal(98765, 'signal: pulser started', 's')
    pulserStopped = Signal(98766, 'signal: pulser stopped', 's')        
        
    ##### SETTINGS #####
    @setting(100, 'Start')
    def start(self,c):
        #if pulser is killed, can't start
        if self._killed:
             raise Error('Pulser is killed. Cannot start.')
             
        dev = self.selectedDevice(c)
        
        def run():
            state = True
            period = yield dev.trigger_period()
            
            #start device and notify
            yield dev.state(0, True)
            self.pulserStarted(dev.name)
            
            #enter loop and initially wait before checking
            #this ordering ensures that checks are delayed
            #and won't begin before pulses actually start
            while state:
                time.sleep(period)
                state = yield dev.run_state()
                
            self.pulserStopped(dev.name)
        
        #this call won't block client
        threads.callMultipleInThread([(run, [], {})])
    
    @setting(102, 'Stop', kill='b')
    def stop(self, c, kill=None):
        yield self.selectedDevice(c).state(0, False)
        if kill:
             self._killed = True
        
    @setting(103, 'Kill', kill='b', returns='b')
    def kill(self, c, kill=None):
        '''
        Kill pulser or query kill state. If killed, the pulser
        will not permit a start to be triggered until the kill
        state is removed.
        
        kill - Set kill state True or False. None queries.
        
        returns - Present kill state
        '''
        if kill:
             yield self.selectedDevice(c).state(0, False)
             self._killed = True
        elif kill is False:
             self._killed = False
             
        returnValue(self._killed)
        
    @setting(113, 'Channel List',
             returns = '*(ws) : List of channel numbers and names')
    def channel_list(self, c):
        chList = yield self.selectedDevice(c).channel_list()
        returnValue(chList)
        
    @setting(114, 'Select Channel',
             channel = [': Get current selection',
                        'w : Select channel by number'],
             returns = ['', 'w : Selected channel number'])
    def select_channel(self, c, channel=None):
        if channel is None:
            try:
                ch = c['Channel']
                return ch
            except Exception, e:
                raise NoChannelSelectedError()
        
        if channel not in self.selectedDevice(c).chMap.keys():
            raise InvalidChannelError()
            
        c['Channel'] = channel
        return c['Channel']
                
    @setting(115, 'List Modes',
             channel = [': List for currently selected channel',
                        'w : List for channel number'],
             returns = '*s : List of supported modes')
    def list_modes(self, c, channel = None):
        dev = self.selectedDevice(c)
        ch = channel if channel is not None else self.selectedChannel(c)
        returnValue(dev.channel_modes(ch))
        
    @setting(116, 'Write Line', line = 's')
    def write_line(self, c, line):
        self.selectedDevice(c).write(line)
        
    @setting(117, 'Read Line', returns='s')
    def read_line(self, c):
        ret = yield self.selectedDevice(c).read()
        returnValue(ret)
        
    @setting(118, 'Query', command = 's', returns='s')
    def query(self, c, command):
        ret = yield self.selectedDevice(c).readWrite(command)
        returnValue(ret)
                
    @setting(201, 'State',
             state = [': Query selected channel state',
                      'b : Enable/disable selected channel'],
             returns = ['', 'b : Selected channel state.'])
    def state(self, c, state=None):
        (dev, ch) = self._sdc(c)
        
        #prevents workaround to enable pulser if killed
        if self._killed and state is True:
             raise Error('Pulser killed. Cannot enable trigger.')
             
        ret = yield dev.state(ch, state)
        returnValue(ret)
        
    @setting(202, 'Width',
             width = [': Query current pulse width',
                      'v[s] : Set pulse width on selected channel'],
             returns=['', 'v[s] : Current pulse width'])
    def width(self, c, width=None):
        (dev, ch) = self._sdc(c)
        ret = yield dev.width(ch, width)
        returnValue(ret)
        
    @setting(203, 'Delay',
             delay = [': Query current delay',
                      'v[s] : Set the delay of selected channel'],
             returns=['', 'v[s] : Current pulse delay'])
    def delay(self, c, delay=None):
        (dev, ch) = self._sdc(c)
        d = yield dev.delay(ch, delay)
        returnValue(d)        
    
    @setting(204, 'Polarity',
             activeHigh = [': Query polarity',
                           'b : Set polarity Active High (False = Low)'],
             returns = ['', 'b : True if Active High, False if Active Low'])
    def polarity(self, c, activeHigh = None):
        dev, ch = self._sdc(c)
        resp = yield dev.polarity(ch, activeHigh)
        returnValue(resp)
        
    @setting(205, 'Output',
             adj = [': Query current mode',
                     'b : True for adjustable voltage out.'],
             voltage = 'v[V]',
             returns = ['', '(bv[V]) : True if adjustable and possible voltage'])
    def output(self, c, adj=None, voltage=None):
        '''Set/query output type.
        
        parameters:
        TTL        None if query, True if TTL, False for Adjustable
        voltage    Provide if setting adjustable (value in Volts)
        
        returns:
        (False, 0)    If TTL output
        (True, Volts)    For adjustable with value in volts
        '''
        
        (dev, ch) = self._sdc(c)
        resp = yield dev.output(ch, adj, voltage)            
        returnValue(resp)
            
    @setting(206, 'Mode',
             mode = [':Query current mode', 's : Mode type'],
             parameter = ['w', '(ww)'],
             returns = ['',
                        '(sw) : Mode with optional parameter',
                        '(s(ww)) : DutyCycle with (on,off) Ns'])
    def mode(self, c, mode = None, parameter = None):
        '''Set/query channel/trigger mode type.
        Possible modes are Normal, Single, Burst, Divide, Duty Cycle.
        Not all modes are supported by all channels on all devices. Call
        list_modes on the channel to see supported types.
        
        parameters:
        mode      None for query, mode type for setting
        parameter Integer N for burst, divide modes
                  Tuple (on, off) for duty cycle
                  
        returns:
        (mode, parameter)   Same format as input.
        '''
        
        #MODE_TYPES not iterable?
        (dev, ch) = self._sdc(c)
        resp = yield dev.mode(ch, mode, parameter)
        returnValue(resp)
        
    @setting(300, 'Run State',
             returns = ['', 'b : Current run state'])
    def run_state(self, c):
        state = yield self.selectedDevice(c).run_state()
        returnValue(state)
    
    @setting(301, 'Trigger Period',
             period = [': Query trigger period',
                       'v[s] : Set trigger period'],
             returns=['', 'v[s] : Current trigger period'])
    def trigger_period(self, c, period = None):
        per = yield self.selectedDevice(c).trigger_period(period)
        returnValue(per)
        
    @setting(302, 'Enable All')
    def enable_all(self, c):   
        dev = self.selectedDevice(c)
        
        for n in dev.chMap.keys():
            if n != 0:
                yield dev.state(n, True)
    
    @setting(303, 'Enable',
             channels = [': Query currently enabled channels',
                         '*w : List of channels to enable'],
             only = 'b : Enable ONLY these channels',
             returns=['', '*w : List of currently enabled channels'])
    def enable(self, c, channels=None, only=False):
        dev = self.selectedDevice(c)
        chSet = set(dev.chMap.keys())
        
        if channels is not None:
            enables = set([ch for ch in channels if ch in chSet])
            disables = chSet - enables if only else set()
            
            for ch in enables:
                yield dev.state(ch, True)
            for ch in disables:
                yield dev.state(ch, False)
            
        onCh = []
        for ch in chSet:
            state = yield dev.state(ch)
            if state:
                onCh.append(ch)
        
        returnValue(onCh)
    
    @setting(304, 'Disable',
             channels='*w : List of channels to disable')
    def disable(self, c, channels=None):
        dev = self.selectedDevice(c)
        chList = dev.chMap.keys()
        
        for c in channels:
            if c in chList:
                yield dev.state(c, False)