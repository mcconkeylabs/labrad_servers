import labrad.units as U
import itertools as IT
import os.path
from threading import Thread
from time import sleep

import config

PULSER_TAG = 'Pulser Server'
PULSER_DEV = 'Pulser Device'
CHMAP_TAG = 'Channel Map'
MCS_TAG = 'MCS Server'

CH_LIST = ['MCS Start', 'MCS Advance', 'Stepper Advance', 'Stepper Direction']
MOVE_CHS = ['Stepper Advance', 'Stepper Direction']

#Channel specific default options for pulser channels
#These values will be overridden when setting up the defaults
#via gen_default_pulse_settings
PULSE_DELAY = U.Value(1, 'ms')
START = {'mode' : 'Single',}
MCS_ADV = {'delay' : PULSE_DELAY,
          }
STEP_ADV = {'delay' : PULSE_DELAY,}
STEP_DIR = {'width' : PULSE_DELAY * 4,}

CH_DEFAULTS_MAP = {'MCS Start' : START,
                   'MCS Advance' : MCS_ADV,
                   'Stepper Advance' : STEP_ADV,
                   'Stepper Direction' : STEP_DIR,
                   }


class LabradController(object):
     reg_path = ['','VUV', 'gui']
     
     def __init__(self, cxn):
          self.cxn = cxn
          self.reg_init()
          self.config = config.DEFAULT_CONFIG
          self.settings = self.gen_default_pulse_settings()
          self.abort_flag = False
          
     @property
     def scan_config(self):
          return self.config
     
     @scan_config.setter
     def scan_config(self, configuration):
          #add verification code
          self.config = configuration
          
     def start(self):
          
          n_reverse = -1*self.config.channels - 1
          reverse = self.config._replace(channels = n_reverse,
                                         dwellTime = config.MIN_DWELL_TIME)
          correct = self.config._replace(channels = 1,
                                         dwellTime = config.MIN_DWELL_TIME)
          
          def genPassCalls(n):
               return [(self.configure_mcs,(self.config, n)),
                       (self.set_move, (self.config,)),
                       (self.start_pulser, ()),
                       (self.wait_pulser, ()),
                       (self.set_move,(reverse,)),
                       (self.start_pulser, ()),
                       (self.wait_pulser, ()),
                       (self.set_move,(correct,)),
                       (self.start_pulser, ()),
                       (self.wait_pulser, ()),
                       (self.configure_scan_reset, ()),
                       ]
               
          call_list = IT.chain([genPassCalls(n) for n in 
                                     range(1, self.config.passes + 1)])
               
          def run_scan(calls):
               for (call, args) in calls:
                    call(*args)
                    if self.abort_flag:
                         return
          
          self.scan_thread = Thread(target = run_scan,
                                    args = (call_list,))
          self.scan_thread.start()
          
                    
     def abort(self):
          self.abort_flag = True
          
          p = self.pulser.packet()
          p.select_channel(0)
          p.state(False)
          p.send()
     
          
     def reg_init(self):
          reg = self.cxn.registry
          
          p = reg.packet()
          p.cd(self.reg_path)
          p.get(PULSER_TAG, key='pulser')
          p.get(PULSER_DEV, key='device')
          p.get(CHMAP_TAG, key='chs')
          p.get(MCS_TAG, key='mcs')
          resp = p.send()
          
          self.pulser = self.cxn[resp['pulser']]
          self.pulser.select_device(resp['device'])
          
          self.mcs = self.cxn[resp['mcs']]
          
          self.ch_map = dict(resp['chs'])
          
     def init_pulser(self):
          pulses = self.gen_default_pulse_settings()
          
          p = self.pulser.packet()
          
          p.select_channel(0)
          p.mode(*config.DEFAULT_TRIGGER_MODE)
          
          for data in pulses.itervalues():
               self.write_packet_data(p, data)
          
          p.send()
          
     def set_move(self, settings=None):
          run = self.config if settings is None else settings
          pulses = self.config2pulse(run)
          
          p = self.pulser.packet()
               
          #configure master trigger settings
          p.select_channel(0)
          p.mode('Burst', abs(run.channels))
          p.trigger_period(U.Value(run.dwellTime, 's'))
          
          #set individual pulse channels
          for data in pulses.itervalues():
               self.write_packet_data(p, data)
          
          p.send()
     
     def gen_default_pulse_settings(self):
          config = dict({k : config.DEFUALT_PULSE_CONFIG for k in CH_LIST})
          
          for (k, elems) in CH_DEFAULTS_MAP.iteritems():
               elems['chno'] = self.ch_map[k]
               config[k] = config[k]._replace(**elems)
          
          return config
     
     
     def config2pulse(self, settings):     
          pulse = self.gen_default_pulse_settings()
          
          steps = abs(settings.channels) * config.ADV_PER_CH
          #duty cycle for MCS for every Nth, 1 on, N-1 off
          dcyc = (1, settings.ratio * config.ADV_PER_CH - 1)
          
          
          replacements = {'Stepper Direction' : {'polarity' : settings.channels >= 0},
                          'Stepper Advance' : {'mode' : ('Burst', steps)},
                          'MCS Advance' : {'mode' : ('DutyCycle', dcyc)},
                          'MCS Start' : {},
                         }
          
          if settings.moveOnly:
               replacements['MCS Advance']['state'] = False
               replacements['MCS Start']['state'] = False
          
          for (ch, data) in replacements.iteritems():
               pulse[ch] = pulse[ch]._replace(**data)
               
          return pulse
     
     @classmethod
     def write_packet_data(cls, p, data):
          p.select_channel(data.chno)
          p.state(data.state)
          p.width(data.width)
          p.delay(data.delay)
          p.mode(*data.mode)
          p.polarity(data.polarity)
          p.output(data.output)
          
     def configure_mcs(self, run_config=None, pass_num=None):
          run = self.config if run_config is None else run_config
          
          mcs_bins = int(run.channels * run.chPerBin)
          
          suffix = '' if pass_num is None else str(pass_num)
          file_name = self.savePattern + suffix + '.mcs'
          file_path = os.path.join(run.saveFolder, file_name)
          
          p = self.mcs.packet()
          p.passes(1)
          p.pass_length(mcs_bins)
          p.acquisition_mode('Rep')
          p.discriminator_level(config.MCS_DISC_LEVEL)
          p.discriminator_edge(True)
          p.input_impedance(True)
          p.dwell(U.Value(0.75, 'V'))
          p.external_trigger(True)
          p.start(file_path)
          p.send()
          
     def start_pulser(self):
          self.pulser.start()
          
     def wait_pulser(self):
          state = self.pulser.run_state()
          while state:
               sleep(self.config.dwellTime / 2)
               
     def configure_scan_reset(self):
          self.init_pulser()