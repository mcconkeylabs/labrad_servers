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

import struct, array
from datetime import datetime
from mcsSettings import *

DATETIME_FORMAT = '%H:%M:%S%m%d%Y'
ACQ_BYTE = {0:'Replace', 1:'Sum', 2:'Replace then Sum'}
DWELL_UNIT = {0:'us', 1:'ms', 2:'s', 3:'ns'}


def byte2internal(byte):
    return 'External' if bool(byte) else 'Internal'

def readMCSFile(fileName):
    with open(fileName, 'rb') as f:
        byteData = f.read()
        
    header = parseHeader(byteData[0:256])
    data = parseData(header, byteData[256:])
    return (header, data)
    
def parseHeader(hBytes):
    start = datetime.strptime(hBytes[20:36], DATETIME_FORMAT)
    header = { 'Pass Length' : struct.unpack('H', hBytes[10:12])[0],
               'Start Time' : start }
    return header

def parseData(header, dataBytes):
    N = header['Pass Length'] * 4
    a = array.array('I')
    a.fromstring(dataBytes[:N])
    return a.tolist()