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
from functools import partial

MODE_TYPES = {'Normal' : 'NORM',
              'Single' : 'SING',
              'Burst' : 'BURS',
              'DutyCycle' : 'DCYC'}

CMODE_TYPES = {'Normal' : 'NORM',
              'Single' : 'SING',
              'Burst' : 'BURS',
              'Divide' : 'DIVI'}

OUTPUT_TYPES = {'TTL' : 'TTL',
                'Adjustable' : 'ADJ',
                '35V' : '35V'}

def bool2str(val):
    return str(int(val))
    
def str2bool(val):
    return bool(int(val))
    
def val2str(typeStr, value):
    return str(value[typeStr])
    
def str2val(typeStr, value):
    return U.Value(float(value), typeStr)
    
def pol2str(isHigh):
    return 'NORM' if isHigh else 'COMP'

def str2pol(val):
    return val == 'NORM'
    
def map2str(typeMap, value):
    return typeMap[value]
    
def str2map(typeMap, value):
    return next(k for (k,v) in typeMap.items() if v == value)
    

TYPE_MAP = {'bool' : (bool2str, str2bool),
            'time' : (partial(val2str, 's'), partial(str2val, 's')),
            'voltage' : (partial(val2str, 'V'), partial(str2val, 'V')),
            'int' : (str, int),
            'polarity' : (pol2str, str2pol),
            'mode' : (partial(map2str, MODE_TYPES), partial(str2map, MODE_TYPES)),
            'cmode' : (partial(map2str, CMODE_TYPES), partial(str2map, CMODE_TYPES)),
            'output' : (partial(map2str, OUTPUT_TYPES), partial(str2map, OUTPUT_TYPES)),
            }