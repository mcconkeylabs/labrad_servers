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
name = BNC Serial Server
version = 1.0
description = Generic BNC Pulser serial server
instancename = %LABRADNODE% BNC Serial Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 67890123
timeout = 20
### END NODE INFO
"""

from labrad.util import getNodeName
from twisted.internet.defer import inlineCallbacks, returnValue
from base_server import BNCBaseServer
from bnc555 import BNC555Serial
from bnc565 import BNC565Serial

DEVICE_MAP = {555 : BNC555Serial, 565 : BNC565Serial}
    
class BNCSerialServer(BNCBaseServer):
    '''
    Generic BNC device server. All pulser types can be run from this.
    Does not include device-specific features (ie. 35V out, multiplexing).
    '''
    
    name = 'BNC Serial Server'
    ID = 54333
    
    nodeDirectory = ['', 'Servers', 'BNC Serial', getNodeName(), 'Links']
    
    @inlineCallbacks
    def initServer(self):
        #read in registry data and then call parent constructor
        reg = self.client.registry()
        yield reg.cd(self.nodeDirectory, True)
        self.rctx = reg.context()
        reg.addListener(self.refreshDeviceList, context=self.rctx)
        yield reg.notify_on_change(self.ID, True)
        
        yield BNCBaseServer.initServer(self)
    
    def serverConnected(self, ID, name):
        if 'serial' in name.lower():
            self.refreshDeviceList()
            
    def serverDisconnected(self, ID, name):
        if 'serial' in name.lower():
            self.refreshDeviceList()
    
    @inlineCallbacks
    def findDevices(self):
        p = self.client.registry.packet()
        p.cd(self.nodeDirectory, True)
        p.dir()
        resp = yield p.send()
        dirs, keys = resp['dir']
        
        p = self.client.registry.packet()
        for k in keys:
            p.get(k, key=k)
        resp = yield p.send()
        
        devList = []
        for serverName in keys:
            if serverName not in self.client.servers:
                continue
            
            server = self.client[serverName]
            portList = yield server.list_serial_ports()
            
            for (model, port, baud) in resp[serverName]:
                if port not in portList:
                    continue
                
                devName = 'BNC%d-%s' % (model, port)
                dev = (devName, (server, port, baud), {})
                devList.append(dev)
            
        returnValue(devList)
                                
    def chooseDeviceWrapper(self, name, *args, **kw):
        model = int(name[3:6])
        return DEVICE_MAP[model]
    
__server__ = BNCSerialServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)