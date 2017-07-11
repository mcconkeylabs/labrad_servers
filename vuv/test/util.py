import mock

from labrad.server import Signal

class MockContext(dict):
    def __init__(self, name='test-context'):
        self.ID = name
        
#class MockPacket(mock.Mock):
#    def __call__(_mock_self, *args, **kwargs):
#        super(MockPacket, _mock_self).__call__(_mock_self, args, kwargs)
#        return _mock_self