import os, os.path

from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.server import LabradServer, setting, Signal
from labrad.errors import Error
import labrad.units as U
from vuv.servers.ortec import jobs, mcsSettings
from vuv.util.files import FileGenerator


PASS_MAX = jobs.PASS_MAX
DWELL_MIN, DWELL_MAX = U.Value(200e-9, 's'), U.Value(5000, 's') 
BIN_MIN, BIN_MAX = mcsSettings.HARDWARE_BOUNDS['PassLen']

class BaseScanner(LabradServer):
     
     @inlineCallbacks
     def initServer(self):
          super(BaseScanner, self).initServer()
          
          yield self._load_registry()
          self.fgen = FileGenerator()
          
     def init_scan(self):
          '''Implement in subclass. Initialization code
          which is run at the beginning of the scan.'''
     
     def scan_pass(self):
          '''Implement in subclass. Represents a single pass of the scan.
          Will be run multiple times corresponding to the number of passes.'''
          
     def end_scan(self):
          '''Implement in subclass. Clean-up code to be run at the end of the
          scan.'''
          
     @inlineCallbacks
     def _load_registry(self):
          reg = self.client.registry
          pass
          p = reg.packet()
          pass
          resp = yield p.send()
          pulserName, devName = resp['pulser']
          mcsName = resp['mcs']
          
          self.pulser = self.client[pulserName]
          yield self.pulser.select_device(devName)
          
          self.mcs = self.client[mcsName]
          self.valut = self.client.data_vault

     @setting(100, 'Start')
     def start(self, ctx):
          pass
    
     @setting(101, 'Stop')
     def stop(self, ctx):
          pass
    
     @setting(110, 'Passes', passes='w', returns='w')
     def passes(self, ctx, passes=None):
          '''
          Set/query number of scan passes.
          
          Input:
               passes - Number of sweeps to make over the scan range
          Returns
               Number of passes
          '''
          if passes is not None:        
               if (passes < 1) or (passes > PASS_MAX):
                    raise Error("Invalid pass number")
               self.npass = passes
          return self.npass
        
     @setting(111, 'Dwell Time', dwell='v[s]', returns='v[s]')
     def dwell_time(self, ctx, dwell=None):
        '''
        Set/query the current dwell time per increment.
        
        Input:
            dwell - Dwell time (in seconds) per increment. Represents smallest increment
                    of the system. (Usually the stepper or energy counter)
        Returns:
            path - Current dwell time
        '''
        
        if dwell is not None:
            if DWELL_MIN <= dwell <= DWELL_MAX:
                self.dwell = dwell
            else:
                raise Error('Dwell time must be between {0} and {1}'
                            .format(DWELL_MIN, DWELL_MAX))
                
        return self.dwell
   
     @setting(112, 'MCS Bins', bins='w', returns='w')
     def mcs_bins(self, ctx, bins=None):
          '''
          Set/query the directory where raw data is saved.
        
          Input:
               path - Directory path to save files to
          Returns:
               path - Current save path
          '''
          if bins is not None:
               if bins < BIN_MIN or bins > BIN_MAX:
                    raise Error('Invalid number of bins')
               else:
                    self.bins = bins
          return bins
        
     @setting(200, 'Save Directory', path='s', returns='s')
     def save_directory(self, ctx, path=None):
        '''
        Set/query the directory where raw data is saved.
        
        Input:
            path - Directory path to save files to
        Returns:
            path - Current save path
        '''
        if path is not None:
             self.fgen.directory = path
        return self.fgen.directory
        
     @setting(201, 'Save File Pattern', pattern='s', returns='s')
     def save_file_pattern(self, ctx, pattern=None):
        '''
        Set/query the current pattern for generating save file names.
        Files will be stored in current 'Save Directory' with a name
        determined by the current pattern. Specify a string containg a *
        (eg. 'data*.mcs') and the * will be updated to give a unique, incremental
        number for each consecutive file. (ie. 'data1.mcs', 'data2.mcs', etc)
        
        Input:
            pattern - Pattern to use. Use a * to indicate where the counter
                      should be placed in string. (eg. 'data*.mcs' -> 
                      'data1.mcs', 'data2.mcs', etc)
        Returns:
            path - Current save pattern
        '''
        if pattern is not None:
             self.fgen.pattern = pattern
        return self.fgen.pattern
     
     
     
     