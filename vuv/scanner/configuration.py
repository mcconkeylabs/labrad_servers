from collections import namedtuple
import labrad.units as U

#setup constants
ADV_PER_CH = 8
DEFAULT_TRIGGER_MODE = ('Burst', 1000)
MIN_DWELL_TIME = 50E-3
MCS_DISC_LEVEL = U.Value(1.5, 'V')

#scan configuration
SCAN_FIELDS = ['channels',
               'passes',
               'dwellTime',
               'chPerBin',
               'saveFolder',
               'savePattern',
               'moveOnly']

ScanConfig = namedtuple('ScanConfig', SCAN_FIELDS)

DEFAULT_SCAN_CONFIG = ScanConfig._make([0,1,1.0,1,'','',False])

#pulser channel configuration
PULSER_FIELDS =  ['chno',
                  'state',
                  'width',
                  'delay',
                  'mode',
                  'polarity',
                  'output',
                  ]

PulseConfig = namedtuple('PulseConfig', PULSER_FIELDS)

DEFAULT_PULSE_CONFIG =   ['0',
                          True,
                          U.Value(10, 'us'),
                          U.Value(0, 's'),
                          'Normal',
                          True,
                          False]

DEFUALT_PULSE_CONFIG = PulseConfig._make(DEFAULT_PULSE_CONFIG)

#default GUI settings
DEFUALT_GUI = {'channels' : 100,
               'passes' : 1,
               'dwellTime' : 1.0,
               'chPerBin' : 1,}