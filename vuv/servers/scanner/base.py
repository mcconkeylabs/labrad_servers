from labrad.server import LabradServer, setting, Signal

class BaseScanner(LabradServer):
    
    @setting(300, 'Start')
    def start(self, ctx):
        pass
    
    @setting(301, 'Stop')
    def stop(self, ctx):
        pass
    
    @setting(310, 'Passes', passes='w')
    def passes(self, ctx):
        pass