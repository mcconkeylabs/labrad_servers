import pytest

import tempfile, os, stat
from shutil import rmtree
from labrad.errors import Error
import labrad.units as U
from vuv.servers.scanner import base

@pytest.fixture(scope='module')
def srv():
     srv = base.BaseScanner()
     return srv

@pytest.fixture
def temp_dir():
     tdir = tempfile.mkdtemp()
     yield tdir
     
     os.chmod(tdir, stat.S_IWRITE)
     if os.listdir(tdir) == []:
          os.rmdir(tdir)
     else:
          rmtree(tdir)

class TestScannerSettings(object):
     @pytest.mark.parametrize('dwell', [1e-9, -0.5, 10e3, 5000.1])
     def test_bad_dwell_time_raises(self, srv, dwell):
          d = U.Value(dwell, 's')
          
          with pytest.raises(Error):
               srv.dwell_time(None, d)
               
     @pytest.mark.parametrize('dwell', [200e-9, 5e3, 100, 0.5, 0.05])
     def test_good_dwell_time_sets(self, srv, dwell):
          d = U.Value(dwell, 's')
          
          ret = srv.dwell_time(None, d)
          
          assert ret == d
          assert srv.dwell == d
          
     @pytest.mark.parametrize('n', [0, -5])
     def test_bad_pass_raises(self, srv, n):
          with pytest.raises(Error):
               srv.passes(None, n)
          
     @pytest.mark.parametrize('n', [1, 10, 100])
     def test_good_pass_sets(self, srv, n):
          ret = srv.passes(None, n)
          
          assert ret == n
          assert srv.npass == n
          
class TestSaveFileGeneration(object):
     @pytest.mark.parametrize('path', ['X:\\'])
     def test_invalid_directory_path_raises(self, srv, path):
          with pytest.raises(Error):
               srv.save_directory(None, path)
               
     @pytest.mark.skip(reason='Cannot change directory permissions for some reason')
     def test_directory_with_no_write_access_raises(self, srv, temp_dir):
          os.chmod(temp_dir, stat.S_IREAD)
          
          with pytest.raises(Error):
               srv.save_directory(None, temp_dir)
               
     @pytest.mark.skip(reason='Cannot change directory permissions for some reason')
     def test_creating_directory_failing_raises(self, srv, temp_dir):
          os.chmod(temp_dir, stat.S_IREAD)
          print stat.S_IMODE(os.stat(temp_dir).st_mode) & stat.S_IWRITE
          
          subpath = os.path.join(temp_dir, 'child')
          
          with pytest.raises(Error):
               srv.save_directory(None, subpath)
               
     
          
     