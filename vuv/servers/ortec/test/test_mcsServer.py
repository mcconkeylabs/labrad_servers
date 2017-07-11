import pytest, mock
from vuv.servers.ortec.mcsServer import SPEC_REGEX

@pytest.mark.parametrize('fileName, number', 
                         [ ('1999_02_03_01.mcs', 1),
                           ('2001_01_01_10.mcs', 10),
                           ('2010_10_10_20.mcs', 20)])
def test_valid_file_regex_matches(fileName, number):
    m = SPEC_REGEX.match(fileName)
    
    assert m != None
    assert int(m.group(1)) == number
    
@pytest.mark.parametrize('fileName', ['test.mcs',
                                      '199_10_10.mcs',
                                      '1999_10_10.txt',
                                      '1234_123_12.mcs',
                                      '1234_12_123.mcs'])
def test_invalid_file_regex_gives_none(fileName):
    m = SPEC_REGEX.match(fileName)
    assert m is None

def test_none_process_not_running(mcs):
    mcs.proc = None
    assert not mcs._isRunning()
    
@pytest.mark.parametrize('retcode', [1, 2, None])
def test_process_running_matches_returncode(mcs, retcode):
    mcs.proc.returncode = retcode
    running = retcode is None
    state = mcs._isRunning()
    
    mcs.proc.poll.assert_called_with()
    assert state == running