import pytest

import labrad.units as U
from labrad.errors import Error
from vuv.servers.scanner import energy

@pytest.fixture
def srv():
     s = energy.EnergyScanner()
     return s

class TestProperties(object):
     @pytest.mark.parametrize('v', [(-1, 5), (10., 11.),
                                    (5, 11), (-2, -1)])
     def test_invalid_voltage_ramp_raises(self, srv, v):
          volts = map(lambda x: U.Value(x, 'V'), v)
          
          with pytest.raises(Error):
               srv.voltage_ramp(None, volts)
               
     @pytest.mark.parametrize('v', [(0, 1), (3, 4.7), (0, 10), (1.5, 9.4)])
     def test_valid_voltage_ramp_sets(self, srv, v):
          volts = map(lambda x: U.Value(x, 'V'), v)
               
          ret = srv.voltage_ramp(None, volts)
          
          assert ret == volts
          assert srv.ramp == volts