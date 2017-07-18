import os, os.path
from time import sleep

from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.server import LabradServer, setting, Signal
from labrad.errors import Error
import labrad.units as U
from vuv.servers.ortec import jobs, mcsSettings
from vuv.util.files import FileGenerator
from vuv.util.stepper import StepperPosition

PASS_MAX = jobs.PASS_MAX
DWELL_MIN, DWELL_MAX = U.Value(200e-9, 's'), U.Value(5000, 's') 
BIN_MIN, BIN_MAX = mcsSettings.HARDWARE_BOUNDS['PassLen']

CH_KEYS = ['MCS_START', 
           'MCS_ADV', 
           'STEP_ADV', 
           'STEP_DIR']

MOVE_DWELL = U.Value(50, 'ms')
SLEEP_TIME = 0.25

class BaseScanner(LabradServer):
     
     @inlineCallbacks
     def initServer(self):          
          yield self._load_registry()
          self.fgen = FileGenerator()
          
          yield LabradServer.initServer(self)
          
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
          
          self.ch_map = dict()
          self.posn = StepperPosition()

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
   
     @setting(210, 'Stepper Position', posn='(ww)', returns='(ww)')
     def stepper_position(self, ctx, posn=None):
          if posn is not None:
               self.posn.set_posn(*posn)
          return (self.posn.channel, self.posn.fraction)
     
     @setting(300, 'Move Stepper', steps=['i', '(ww)'], returns='(ww)')
     def move_stepper(self, steps):
          '''
          Move the stepper motor a given number of steps or to a specific
          channel position. Input may be
          
          integer - Number of steps to move. Input a negative value to
                    move backwards
          (ch, frac) - Giving the channel number and fraction of a channel
                       (each channel divided into 8)
          
          Returns the new channel position (ch, frac)
          '''
          
          if steps is int:
               dx = StepperPosition(0, steps)
               newPos = self.posn + dx
          else:
               newPos = StepperPosition().set_posn(*steps)
          
          if newPos.toinc() < 0:
               outStr = 'Invalid position ({0}, {1}) on stepper'\
                         .format(newPos.channel, newPos.fraction)
               raise Error(outStr)
          
          is_fwd = steps >= 0
          N = abs(steps)
          
          @inlineCallbacks
          def run_pulser():
               enabled = yield self.pulser.enable()
               ons = map(lambda x: self.ch_map[x], ['STEP_DIR, STEP_ADV'])
               yield self.pulser.enable(ons, True)
               
               yield self._step_adv_setup()
               yield self._step_dir_setup(is_fwd)
               
               yield self._trigger_setup(MOVE_DWELL, N)
               
               #need to start pulser and run monitor in loop or get
               #signal from pulser
               yield self.pulser.start()
               
               while (yield self.pulser.run_state()):
                    sleep(SLEEP_TIME)
          
               yield self.pulser.enable(enabled, True)
          
     @inlineCallbacks
     def _mcs_start_setup(self):
          p = self.pulser.packet()
          
          p.select_channel(self.ch_map['MCS_START'])
          p.state(True)
          p.width(U.Value(10, 'us'))
          p.delay(U.Value(10, 'us'))
          p.mode('Single')
          p.polarity(True)
          p.output(False)
          
          yield p.send()
     
     def _mcs_adv_setup(self, on, off):
          p = self.pulser.packet()
          
          p.select_channel(self.ch_map['MCS_ADV'])
          p.state(True)
          p.width(U.Value(10, 'us'))
          p.delay(U.Value(10, 'us'))
          p.mode('DutyCycle', (on, off))
          p.polarity(True)
          p.output(False)
          
          yield p.send()
          
     def _step_adv_setup(self):
          p = self.pulser.packet()
          
          p.select_channel(self.ch_map['STEP_ADV'])
          p.state(True)
          p.width(U.Value(10, 'us'))
          p.delay(U.Value(10, 'us'))
          p.mode('Normal')
          p.polarity(True)
          p.output(False)
          
          yield p.send()
          
     def _step_dir_setup(self, forward=True):
          p = self.pulser.packet()
          
          p.select_channel(self.ch_map['STEP_DIR'])
          p.state(forward)
          p.width(U.Value(1, 'ms'))
          p.delay(U.Value(0, 's'))
          p.mode('Normal')
          p.polarity(True)
          p.output(False)
          
          yield p.send()       
          
     def _trigger_setup(self, dwell, pulses):
          p = self.pulser.packet()
          
          p.select_channel(0)
          p.trigger_period(dwell)
          p.mode('Burst', pulses)
          
          yield p.send()
          
     def _mcs_setup(self):
          p = self.mcs.packet()
          
          p.pass_length(self.bins)
          p.sweeps(self.passes)
          p.acquisition_mode('Rep')
          p.discriminator_edge(True)
          p.input_impedance(True)
          p.dwell(U.Value(0.5, 'V'))
          p.external_trigger(True)
          
          #the discriminator level needs to be configured
          #currently save path is configured in mcs.start()
          #this needs to be fixed
          pass
          
          yield p.send()