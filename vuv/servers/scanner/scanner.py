import labrad.units as U
from labrad.server import LabradServer, Signal, setting
from labrad.errors import Error
from twisted.internet.defer import inlineCallbacks, returnValue
from itertools import chain

from vuv.servers.stepper.calc import isValidCh
from vuv.servers.stepper.stepper import InvalidPositionError

ADV_PER_CH = 8.0
MIN_RATIO = 1 / ADV_PER_CH
MIN_DWELL = U.Value(50, 'ms') * ADV_PER_CH

CHANNELS = ['Adv', 'Trigger']
DEVICES = ['MCS', 'Pulser', 'Stepper']
REG_PATH = ['', 'Servers', 'VUV Scanner']

PARAMETER_DEFAULTS = {'Dwell Time' : U.Value(1.0, 's'),
                      'Bin Ratio' : 1.0,
                      'Passes' : 1,
                      'Scan Range' : ((1000, 0), (2000, 0))}

def rat2dcyc(ratio):
    inc = int(ratio * ADV_PER_CH)
    doff = inc - 1
    return (1, doff)
    
class ScanServer(LabradServer):
    name = 'Scan Server'
    ID = 67545
    
    #slot IDs
    pulserStartID = 212233
    pulserStopID = 212234
    
    _paramMap = {'Dwell Time' : 'dwell',
                 'Bin Ratio' : 'ratio',
                 'Passes' : 'passes',
                 'Scan Range' : 'range'}
                 
    onPassComplete = Signal()
    
    def initServer(self):
        pass
    
    def stopServer(self):
        pass
    
    @inlineCallbacks
    def _loadRegistryData(self):
        p = self.client.registry.packet()
        p.cd(REG_PATH)
        for d in DEVICES:
            p.get(d, key=d)
        for (k, v) in PARAMETER_DEFAULTS.iteritems():
            p.get(k, True, v, key=k)
        resp = yield p.send()
        
        #unpack serve and device names
        dev, srv = resp['Pulser']
        self.pulser = self.client[srv]
        yield self.pulser.select_device(dev)
        
        self.mcs = self.client[resp['MCS']]
        self.stepper = self.client[resp['Stepper']]
        
        #assign parameters to respective values
        for (k, v) in ScanServer._paramMap.iteritems():
            setattr(self, v, resp[k])
            
    @inlineCallbacks
    def _updateRegistry(self):
        p = self.client.registry.packet()
        for k in ScanServer._paramMap.iterkeys():
            p.set(k, getattr(self, k))
        yield p.send()
        
    
    
    @setting(200, 'Start')
    def start(self, c):
        pass
    
    @setting(201, 'Stop')
    def stop(self, c):
        pass
    
    @setting(300, 'Dwell Time', dwell='v[s]', returns='v[s]')
    def dwell_time(self, c, dwell=None):
        '''
        Set/query the dwell time per MCS bin.
        Input:
            dwell - Dwell time in seconds per MCS bin. None for query
        Returns:
            Current dwell time per bin in seconds.
        '''
        
        if dwell is not None:
            if dwell <= MIN_DWELL:
                raise Error('Dwell time must be at least %f' % MIN_DWELL['s'])
            self.dwell = dwell
            
        return self.dwell
        
    @setting(301, 'Channel Ratio', ratio='v[]', returns='v[]')
    def channel_ratio(self, c, ratio=None):
        '''
        Set/query current channel ratio. Defines the number of
        stepper channels per MCS bin. Minimum must be 1/8 or 0.125.
        
        Input:
            ratio - Ratio to set. None if querying.
        Returns:
            Current ratio as floating point number
        '''
        if ratio is not None:
            if ratio < MIN_RATIO:
                raise Error('Channel ratio must be at least %f' % MIN_RATIO)
            
            #round to nearest increment
            ratio -= (ratio % MIN_RATIO)
            self.ratio = ratio
        return self.ratio
        
    
    @setting(302, 'Passes', passes='w', returns='w')
    def passes(self, c, passes=None):
        '''
        Set/query number of scan passes.
        
        Input:
            passes - Number of sweeps to make over the scan range
        Returns
            Number of passes
        '''
        
        if passes is not None:
            if passes < 1:
                raise Error('Invalid pass number')
            self.passes = passes
        return self.passes
        
    
    @setting(303, 'Scan Range', start=['w','(ww)'], stop=['w', '(ww)'],
             returns=['*(ww)'])
    def scan_range(self, c, start=None, stop=None):
        '''
        Set/query scan channel range.
        
        Input:
            start - Channel to start scan at. Can be integer identifying start
                    channel or a tuple (channel, partial) for partial channel increment.
                    
            stop -  Channel to stop at. Same format as start channel.
        Returns:
            [start, stop] - Scan pass bounds as a tuple. Both channels are returned
                            as tuple elements (channel, partial) where partial
                            indicates 8ths of a channel. (ie. partial=5 is 5/8 of
                            a channel)
        '''
        
        if start is not None:
            if stop is None:
                raise Error('Must inclide stop channel.')
            elif (not isValidCh(start)) or (not isValidCh(stop)):
                raise InvalidPositionError()
                
            if type(start) is not tuple:
                start = (start, 0)
            if type(stop) is not tuple:
                stop = (stop, 0)
                
            self.range = (start, stop)
            
        return self.range
        
    