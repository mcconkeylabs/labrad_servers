import pytest
import random
from mock import Mock, MagicMock

from .. import controller

TRUE_WEIGHT = 0.05

class MockPulser(Mock):
     def run_state(self):
          rnd = random.random()
          return rnd < TRUE_WEIGHT
     
     def packet(self):
          return Mock()
     
class NoContactController(controller.LabradController):
     def reg_init(self):
          self.pulser = MockPulser()
          self.mcs = Mock(packet = Mock())
          self.ch_map = {k : 0 for k in controller.CH_LIST}
          

@pytest.fixture
def ctrl():
#     control = mocker.patch.object(controller.LabradController, 'reg_init')
#     control.pulser = MockPulser()
#     control.mcs = Mock(packet = Mock())
#     control.ch_map = {k : 0 for k in controller.CH_LIST}
     return NoContactController(None)

class TestStartCall(object):
     @pytest.fixture(autouse=True)
     def setup(self, ctrl, mocker):
          self.ctrl = ctrl
          self.thread = mocker.patch('controller.Thread')
          
     @pytest.mark.parametrize('count', range(5, 5, 50))
     def test_sets_correct_number_of_passes(self, count):
          self.ctrl.config = self.ctrl.config._replace(passes = count)
          self.ctrl.start()
          
          args, kwargs = self.thread_mock.call_args
          call_list = kwargs['args'][0]
     
          assert len(call_list) == count
          
     def test_starts_call(self):
          self.ctrl.start()
          self.thread_mock.assert_called_once()
          
class TestInitPulser(object):
     do_something = None
     
class TestDefaultPulseSettingGen(object):
     @pytest.fixture(autouse=True)
     def setup(self, ctrl):
          self.ctrl = ctrl
          
     def test_channels_map(self):
          ch_map = {k : random.randint(1,10) for k in controller.CH_LIST}
          self.ctrl.ch_map = ch_map
          
          ret = self.ctrl.gen_default_pulse_config()
          
          for (ch, num) in ch_map.iteritems():
               pytest.assume(ret[ch].chno == num, '{} : {} != {}'.format(ch, ret[ch].chno, num))
          
     @pytest.mark.parametrize('ch_tpl', controller.CH_DEFAULTS_MAP.iteritems())
     def test_non_defaults_replaced(self, ch_tpl):
          ch_name, items = ch_tpl
          
          ret = self.ctrl.gen_default_pulse_config()
          
          #check that all of the items have been replaced
          for (k, v) in items.iteritems():
               pytest.assume(ret[k] == v, '({}) {} != {}'.format(k, ret[k], v))
               
     @pytest.mark.parametrize('ch_tpl', controller.CH_DEFAULTS_MAP.iteritems())
     def test_defaults_not_replaced(self, ch_tpl):
          ch_name, items = ch_tpl
          default = controller.configuration.DEFAULT_PULSE_CONFIG
          
          ret = self.ctrl.gen_default_pulse_config()
          
          unchanged = set(default.keys()) - set(ret.keys())
          for k in unchanged:
               pytest.assume(ret[k] == default[k], '({}) {} != {}'.format(k, ret[k], default[k]))