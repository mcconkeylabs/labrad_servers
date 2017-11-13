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
name = OrtecMCS Server
version = 1.0
description = Server for an Ortec MCS-PCI card
instancename = %LABRADNODE% OrtecMCS Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 5678901234
timeout = 20
### END NODE INFO
    
Class for Ortec MCS-PCI Multi-channel scaler card
"""

import tempfile as T
import labrad.units as U
import datetime as D
import os, re, time
import os.path as OP
from itertools import chain
from shutil import rmtree
from subprocess import call, Popen
from time import sleep
from labrad.server import LabradServer, setting, Signal
from labrad.errors import Error
from labrad.util import getNodeName
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import callMultipleInThread
import jobs

DATE_FMT = '%Y_%m_%d'                    
SPEC_REGEX = re.compile('\d{4}_\d{2}_\d{2}_(\d{2})\.mcs')
EXE_DEFAULT = 'C:\Program Files\Mcs32\Mcs32.exe'
JOB_NAME = 'job.job'
SAVE_NAME = 'scan.dat'
SAVE_DEFAULT = '.'

ACQ_MODES = ['Rep', 'Sum', 'RepSum']

DEFAULT_PARAMETERS = {'Length' : 1024,
                      'Passes' : 1,
                      'AcqMode' : 'RepSum',
                      'DiscLevel' : U.Value(0.5, 'V'),
                      'DiscEdge' : 'Rising',
                      'Impedance' : True,
                      'Ramp' : [U.Value(0.0, 'V')],
                      'DwellTime' : (False, U.Value(0.5, 's')),
                      'DwellTrigger' : (True, U.Value(0.5, 'V')),
                      'ExtTrigger' : False
                     } 
                     
def dateString():
    return D.datetime.now().strftime('%Y_%m_%d')
    
class MCSRunningError(Error):
    '''The MCS is currently running'''
    code = 10

class MCSServer(LabradServer):
    
    name = '%LABRADNODE% OrtecMCS Server'
    ID = 654321
    
    regPath = ['', 'Servers', 'OrtecMCS', getNodeName()]    
    
    ##### SIGNALS #####    
    onScanStart = Signal(66777, 'signal: scan started', 's')
    onScanComplete = Signal(66778, 'signal: scan complete', 's')
    
    @inlineCallbacks
    def initServer(self):
        print "Init mcs"
        self.reg = self.client.registry
        yield self._loadRegistry()
        print "Loaded registry"
        
        self.tmpDir = T.mkdtemp()
        self.jobPath = OP.join(self.tmpDir, JOB_NAME)
        self._killed = False
        
        yield LabradServer.initServer(self)
        
    @inlineCallbacks
    def stopServer(self):
        yield self._updateRegistry()
        rmtree(self.tmpDir)
        
    @inlineCallbacks
    def _loadRegistry(self):
        p = self.reg.packet()
        p.cd(self.regPath, True)
        p.get('ExePath', True, EXE_DEFAULT, key='exe')
        p.cd('Settings', True)
        for (k, v) in DEFAULT_PARAMETERS.items():
            p.get(k, True, v, key=k)
        resp = yield p.send()
        
        #parse response
        self.exePath = resp['exe']
        self.params = dict([(k, resp[k]) for k in\
                            DEFAULT_PARAMETERS.keys()])
                            
        print self.params
    
    @inlineCallbacks
    def _updateRegistry(self):
        p = self.reg.packet()
        p.cd(self.regPath, True)
        p.set('ExePath', self.exePath)
        p.cd('Settings')
        for (k,v) in self.params.items():
            p.set(k, v)
        yield p.send()
        
    def _runJob(self, lines):
        #write job file
        output = ['SET_MCS 1'] + lines
        with open(self.jobPath, 'w') as job:
            job.write('\n'.join(output))
            
        #execute MCS program with job file
        args = [self.exePath, '-J', self.jobPath]
        self.proc = Popen(args)
        
    def _isRunning(self):
        if hasattr(self, 'proc'):
            return self.proc.poll() is None
        else:
            return False
            
    def _monitorScan(self):
        def run():
            while self.proc.poll() is None:
                sleep(0.5)
            path = self._savePath()
            self.onScanComplete(path)
                
        cmds = [(run, [], {})]
        callMultipleInThread(cmds)
            
    ###OVERWRITES OLD SCAN. INEFFICIENT TO KEEP GENERATING!!!
    def _savePath(self):
        path = os.path.join(self.tmpDir, SAVE_NAME)
        return path
        
    
    
    ##### SETTINGS #####
    @setting(100, 'Pass Length', length = 'w', returns = 'w')
    def pass_length(self, c, length=None):
        '''Set/query the number of bins in the scan pass. (None queries)'''
        if length is not None:
            if length < jobs.LEN_MIN or length > jobs.LEN_MAX:
                string = 'Pass length must be between %d and %d' %\
                         (jobs.LEN_MIN, jobs.LEN_MAX)
                raise Error(string)
                
            self.params['Length'] = length   
            
        return self.params['Length']
    
    @setting(101, 'Passes', passes = 'w', returns='w')
    def passes(self, c, passes=None):
        '''Set/query the number of scan sweeps. (None queries)'''
        if passes is not None:
            if passes < jobs.PASS_MIN or passes > jobs.PASS_MAX:
                string = 'Pass count must be between %d and %d'\
                         % (jobs.PASS_MIN, jobs.PASS_MAX)
                raise Error(string)
                
            self.params['Passes'] = passes
            
        return self.params['Passes']
    
    @setting(102, 'Acquisition Mode', mode='s', returns='s')
    def acquisition_mode(self, c, mode = None):
        '''Set/query acquisition mode. 
        
        Input
        None : Query current setting
        Mode : Set mode to one of 'Rep', 'Sum', 'RepSum'
        
        Returns
        Currently set acquisition mode.
        '''
        if mode is not None:
            if mode not in ACQ_MODES:
                opts = ', '.join(ACQ_MODES)
                string = 'Acquisition mode must be one of %s' % opts
                raise Error(string)
            self.params['AcqMode'] = mode
            
        return self.params['AcqMode']
    
    @setting(103, 'Discriminator Level', level='v[V]', returns='v[V]')
    def discriminator_level(self, c, level=None):
        '''Set/query current discriminator voltage'''
        if level is not None:
            if level['V'] < jobs.DISC_MIN or level['V'] > jobs.DISC_MAX:
                string = 'Discriminator level must be between %f and %f'\
                         % (jobs.DISC_MIN, jobs.DISC_MAX)
                raise Error(string)
            self.params['DiscLevel'] = level
            
        return self.params['DiscLevel']
    
    @setting(104, 'Discriminator Edge', 
             rising=['s: Rising or Falling',
                     'b: True for rising edge'],
             returns='s: Current edge')
    def discriminator_edge(self, c, rising=None):
        '''Set/query input channel discriminator edge. 
        
        None queries input. Can be set with edge type
        'Rising' or 'Falling' or by
        True/False for rising/falling edge.
        
        Returns the edge type as text
        '''
        if rising is not None:
            if type(rising) is str:
                rStr = rising.lower()
                if rStr not in ['rising', 'falling']:
                    
                    rvals = ', '.join(['Rising', 'Falling'])
                    raise Error('Edge must be one of %s' % rvals)
                else:
                    rVal = rStr == 'rising'
            else:
                rVal = rising
                
            self.params['DiscEdge'] = rVal
            
        return 'Rising' if self.params['DiscEdge'] else 'Falling'
        
    @setting(105, 'Input Impedance', 
             imped=['v[Ohm]: Impedance value (50 or 1K)',
                    'b: True for 50 Ohms'], 
             returns='v[Ohm]: Current input impedance')
    def input_impedance(self, c, imped=None):
        '''Set/query input signal impedance
        
        None : Query current setting
        True : Input at 50 Ohm impedance
        False : Input at 1 kOhm impedance
        Value can also be actual impedance value
        
        Returns : Impedance value
        '''
        if imped is not None:
            if type(imped) is bool:
                val = imped
            else:
                if imped['Ohm'] not in [50, 1000]:
                    raise Error('Impedance must be 50, 1000 Ohms or boolean')
                else:
                    val = imped['Ohm'] == 50
            
            self.params['Impedance'] = val
            
        return U.Value(50 if self.params['Impedance'] else 1000, 'Ohm')
    
    @setting(106, 'Voltage Ramp', 
             start='v[V]', stop='v[V]', middle='v[V]', 
             returns='*v[V]')
    def voltage_ramp(self, c, start=None, stop=None, middle=None):
        if start is not None:
            vs = [start, stop, middle]
            self.params['Ramp'] = [v for v in vs if v is not None]
        return self.params['Ramp']
    
    @setting(107, 'Dwell Time',
             dTime = 'v[s]', returns = '(bv[s])')
    def dwell_time(self, c, dTime=None):
        '''Set/query dwell time and trigger.
        Input :
        time - Dwell time per pass in seconds. If None, returns current settings
        
        Returns:
        (state, time) - state is True if internal dwell time set
                        time is current dwell time setting
        '''
        if dTime is not None:
            if (dTime['s'] < jobs.DWELL_MIN) or (dTime['s'] > jobs.DWELL_MAX):
                print '1 - {} AND 2 - {}'.format(dTime['s'] < jobs.DWELL_MIN, dTime['s'] > jobs.DWELL_MAX)
                string = 'Dwell time {} must be between {} and {}'.format(dTime['s'], jobs.DWELL_MIN, jobs.DWELL_MAX)
                raise Error(string)
            
            #enable internal trigger and disable external
            self.params['DwellTime'] = (True, dTime)
            
            _, thresh = self.params['DwellTrigger']
            self.params['DwellTrigger'] = (False, thresh)
            
        return self.params['DwellTime']
        
    @setting(108, 'Dwell Trigger', dTrig = 'v[V]', returns='(bv[V])')
    def dwell_trigger(self, c, dTrig=None):
        '''Set/query external dwell trigger.
        Input:
        dTrig - Trigger threshold in votes. None will query current setting.
        
        Returns:
        (state, trigger) - state is True if external dwell trigger set
                           trigger is current external dwell threshold
        '''
        if dTrig is not None:
            if dTrig['V'] < jobs.DISC_MIN or dTrig['V'] > jobs.DISC_MAX:
                print '1 - {} AND 2 - {}'.format(dTrig['V'] < jobs.DISC_MIN, dTrig['V'] > jobs.DISC_MAX)
                string = 'Dwell time {} must be between {} and {}'.format(dTrig['s'], jobs.DISC_MIN, jobs.DISC_MAX)
                raise Error(string)
            
            #enable external trigger and disable internal
            self.params['DwellTrigger'] = (True, dTrig)
            
            _, per = self.params['DwellTime']
            self.params['DwellTime'] = (False, per)
            
        return self.params['DwellTrigger']
        
    @setting(110, 'External Trigger',
             external = 'b', returns='b')
    def external_trigger(self, c, external=None):
        '''Set/query start trigger setting.
        None queries, True/False for External/Internal trigger
        '''
        if external is not None:
            self.params['ExtTrigger'] = external
        return self.params['ExtTrigger']
    
    @setting(200, 'Start', path='s: Save path')
    def start(self, c, path=None):
        '''Start the MCS with the current settings. Will raise an error
        if the MCS is killed, will raise an error if started.
        
        path: File name or directory to place .mcs spectrum file.
              Defaults to None in which case currently set directory is used.
              If directory provided, saves file with format
              YY_MM_DD_NN.mcs    where NN increments with successive saves
        '''
        if self._isRunning():
            return
        elif self._killed:
            raise Error('MCS killed. Cannot start.')
            
#        sp = path if path is not None else self._savePath()
#        lines = list(chain(jobs.parameterLines(self.params),
#                           jobs.SCAN_LINES, [jobs.saveLine(sp)]))
        lines = list(chain(jobs.parameterLines(self.params),
                           jobs.SCAN_LINES))
        if path is not None:
             lines.append(jobs.saveLine(path))
             
        self._runJob(lines)
        self.onScanStart(path)
        self._monitorScan()
    
    @setting(201, 'Stop', kill='b')
    def stop(self, c, kill=None):
        '''Stop the current run.
        kill - True if MCS should also be killed
        '''
        if self._isRunning():
            self.proc.terminate()
        if kill:
             self._killed
            
    @setting(202, 'Kill', kill='b', returns='b')
    def kill(self, c, kill=None):
        '''
        Kill the MCS or query kill state. If killed, MCS
        will raise an error if started.
        '''
        if kill:
             yield self.stop(c)
             self._killed = True
        elif kill is False:
             self._killed = False
             
        returnValue(self._killed)
    
    @setting(212, 'Clear')
    def clear_buffer(self, c):
        '''Clear all data in the hardware buffers. 
        Will not clear if the device is running.'''
        if self._isRunning():
            raise MCSRunningError()
        self._runJob(jobs.CLEAR_LINES)
        
    @setting(213, 'Run State', returns='b')
    def run_state(self, c):
        '''Current MCS run state.'''
        return self._isRunning()
        
    #THIS IS NO GOOD. NEED TO SAVE LOCATION TO PASS ON
    #DOES NOT PROCESS BINARY FILE!!!
    @setting(214, 'Save Data', path='s', returns='s')
    def save_data(self, c, path=None):
        '''Save current MCS buffer to specified path. Writes to default
        otherwise.'''
        
        if self._isRunning():
            raise MCSRunningError()
        sp = path if path is not None else self._savePath()
        lines = ['SET_MCS 1', jobs.saveLine(sp)]
        self._runJob(lines)
        
__server__ = MCSServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)