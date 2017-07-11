import mock

from labrad.server import Signal

class MockContext(dict):
    def __init__(self, name='test-context'):
        self.ID = name