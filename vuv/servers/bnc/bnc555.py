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

from base_bnc import BNCPulser, BNCSerial, MODE_TYPES
from twisted.internet.defer import inlineCallbacks, returnValue

CMODE_TYPES = {'Normal' : 'NORM',
              'Single' : 'SING',
              'Burst' : 'BURS',
              'Divide' : 'DIVI'}
              
CMODE_LOOKUP = dict([(v, k) for (k,v) in CMODE_TYPES.items()])


class BNC555Pulser(BNCPulser):
    def channel_modes(self, ch):
        return CMODE_TYPES.keys() if ch != 0 else MODE_TYPES.keys()
        
    @inlineCallbacks
    def mode(self, ch, mType = None, modeParameter = None):
        tag, modeType = (':MODE', 'mode') if ch == 0 else (':CMODE', 'cmode')
        modeVal = yield self._param(tag, mType, modeType, ch)
        
        if modeVal == 'Burst':
            param = yield self._param(':BCO', modeParameter,'int', ch)
        elif modeVal == 'Divide':
            param = yield self._param(':DCO', modeParameter, 'int', ch)
        else:
            param = 0
            
        returnValue((modeVal, param))
        
class BNC555Serial(BNC555Pulser, BNCSerial):
    pass