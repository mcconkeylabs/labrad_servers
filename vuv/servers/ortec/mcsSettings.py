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

import labrad.units as U

def str2dwell(string):
    return float(string) if string != '0' else 0L
    
def ramp2str(ramp):
    if len(ramp) == 2:
        string = '2 %f 0 %f' % (ramp[0]['V'], ramp[1]['V'])
    else:
        string = '3 %f %f %f' % (ramp[0]['V'], ramp[1]['V'], ramp[2]['V'])
    return string
    
def str2ramp(string):
    elems = string.split(' ')
    N = int(elems[0])
    include = [1, 3] if N == 2 else [1, 2, 3]
    fn = lambda x: U.Value(float(elems[x]), 'V')
    ramp = tuple([fn(x) for x in include])
    return ramp

DISPLAY_HEADER = '[Display]'
DISPLAY_SETTINGS = {'LogScale' : bool,
                    'WrapMode' : bool,
                    'Graticule' : bool,
                    'FullView' : bool,
                    'FillMode' : bool,
                    'Start' : int,
                    'nBins' : int,
                    'HScale' : int,
                    'VScale' : int,
                    'Marker' : int,
                    'xProportion' : float,
                    'yProportion' : float,
                    'xRelation' : float,
                    'yRelation' : float,
                    'FvColors' : list,
                    'EvColors' : list
                   }
                 
HARDWARE_HEADER = '[Hardware]'
HARDWARE_SETTINGS = {'PassLen' : int,
                     'Preset' : int,
                     'Dwell' : 'dwell',
                     'SumMode' : bool,
                     'LLSCA' : 'voltage',
                     'ULSCA' : 'voltage',
                     'DiscV' : 'voltage',
                     'DiscRise' : bool,
                     'InpImpFifty' : bool,
                     'ExtDwlThrsh' : 'voltage',
                     'RepSum' : bool,
                     'ExtTrig' : bool,
                     'InpSel' : bool,
                     'Ramp' : 'ramp'
                    }
                    
HARDWARE_BOUNDS = { 'PassLen' : (4, 65536),
                    'DwellTime' : (5e-9, 65535),
                    'DiscV' : (-1.6, 3.0),
                    'ExtDwlThrsh' : (-1.6, 3.0),
                    'Ramp' : (0.0, 10.0),
                    'LLSCA' : (0.0, 10.0),
                    'ULSCA' : (0.0, 10.0)
                  }
                    
PARSERS = {bool : (lambda x: str(int(x)), 
                   lambda x: bool(int(x))),
           int : (str, int),
           float : (str, float),
           list : (lambda x: ', '.join([str(e) for e in x]), 
                   lambda x: [int(e) for e in x.split(', ')]),
           'dwell' : (str, str2dwell),
           'ramp' : (ramp2str, str2ramp),
           'voltage' : (lambda x: str(x['V']),
                        lambda x: U.Value(float(x), 'V'))
          }
          
#acqusition modes with associated 'SumMode' and 'RepSum' values
ACQ_MODES = {'Replace' : (False, False),
             'Sum' : (True, False),
             'RepSum' : (True, True)
             }