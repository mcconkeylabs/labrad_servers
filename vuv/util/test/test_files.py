import pytest

import os, stat
import itertools as I
from tempfile import mkdtemp
from shutil import rmtree
from labrad.errors import Error
from vuv.util import files

GEN_PATTERN = 'data*.txt'
BASE_PATH = 'data1.txt'

@pytest.fixture(scope='function')
def temp_dir():
     tdir = mkdtemp()
     yield tdir
     
     os.chmod(tdir, stat.S_IWRITE | stat.S_IREAD)
     if not any(os.listdir(tdir)):
          os.rmdir(tdir)
     else:
          rmtree(tdir)

@pytest.fixture
def gen(temp_dir):
     g = files.FileGenerator(temp_dir, GEN_PATTERN)
     
     flist = os.listdir(g.directory)
     if any(flist):
          for f in flist:
               os.remove(os.path.join(g.directory, f))
     return g

BUILD_RANGE = list(I.chain(range(1,11,2), [50, 200]))
@pytest.fixture(params= BUILD_RANGE)
def build_list(request, gen):
     n = request.param
     fnames = I.imap(TestFileGeneratorGeneration.file_pattern, range(n))
     paths = I.imap(lambda n: os.path.join(gen.directory, n), fnames)
     for p in paths:
          with open(p, 'a') as f:
               f.write(' ')
               
     yield n
     
     for p in paths:
          os.remove(p)
          

def file_cases():
     GOOD_LIST = ['data*.txt', '*.txt', 'help*me.please']
     BAD_LIST = ['where.star', 'were.bear', '5*.', '*']
     
     PAIRS = [(True, GOOD_LIST), (False, BAD_LIST)]
     lf = lambda (x, y): list(I.izip_longest(y, [], fillvalue=x))
     CASES = I.chain(map(lf, PAIRS))
     return list(CASES)

class TestFileRegexPattern(object):
#
#     @pytest.mark.skip(reason='Cannot get list generating properly')     
#     @pytest.mark.parametrize('string, result', file_cases())
#     def test_regex_pattern_matches_correctly(self, string, result):
#          match = files.PATTERN_REGEX.match(string)
#          
#          assert result == bool(match)
          
     @pytest.mark.parametrize('string, parts', [('a*b.c', ('a','b','.c')),
                                                ('h*.txt', ('h', '', '.txt')),
                                                ('*.pass', ('','','.pass'))])
     def test_regex_pattern_groups_correctly(self, string, parts):
          match = files.PATTERN_REGEX.match(string)
          
          assert parts == match.groups()
          
class TestFileGeneratorProperties(object):
     @pytest.mark.parametrize('string, parts', [('a*b.c', ('a','b','.c')),
                                                ('h*.txt', ('h', '', '.txt')),
                                                ('*.pass', ('','','.pass'))])
     def test_pattern_stores_correctly(self, gen, string, parts):
          gen.pattern = string
          
          assert gen.pattern == string
          assert (gen._pre, gen._mid, gen._suff) == parts
          
     @pytest.mark.parametrize('string', ['where.star', 'were.bear', '5*.', '*'])
     def test_bad_pattern_raises(self, gen, string):
          with pytest.raises(Error):
               gen.pattern = string

     @pytest.mark.parametrize('path', ['X:\\'])
     def test_invalid_directory_path_raises(self, gen, path):
          with pytest.raises(Error):
               gen.directory = path
               
     @pytest.mark.skip(reason='Cannot change directory permissions for some reason')
     def test_directory_with_no_write_access_raises(self, gen, temp_dir):
          os.chmod(temp_dir, stat.S_IREAD)
          
          with pytest.raises(Error):
               gen.directory = temp_dir
               
     @pytest.mark.skip(reason='Cannot change directory permissions for some reason')
     def test_creating_directory_failing_raises(self, gen, temp_dir):
          os.chmod(temp_dir, stat.S_IREAD)
          print stat.S_IMODE(os.stat(temp_dir).st_mode) & stat.S_IWRITE
          
          subpath = os.path.join(temp_dir, 'child')
          
          with pytest.raises(Error):
               gen.directory = subpath
               
class TestFileGeneratorGeneration(object):      
     def test_empty_folder_generates_init_case(self, gen):                    
          path = gen.generate_path()
          
          assert path == BASE_PATH
          
     def test_counter_increments_with_files(self, gen, build_list):
          expected = TestFileGeneratorGeneration.file_pattern(build_list)
          ret = gen.generate_path()
          
          assert ret == expected
          
     def test_irrelevant_files_ignored(self, gen):
          fpath = 'junk.txt'
          with open(fpath, 'a'):
               os.utime(fpath, None)
               
          ret = gen.generate_path()
          
          assert ret == BASE_PATH
          
     @pytest.mark.parametrize('n', BUILD_RANGE)
     def test_pattern_regex_matches_files(self, gen, n):
          fname = TestFileGeneratorGeneration.file_pattern(n)
          
          match = gen._regex.match(fname)
          assert match.group(1) == str(n)
          
     @pytest.mark.parametrize('string', ['bad', 'data.txt', 
                                         'nope1.dat', '1.dat'])
     def test_pattern_regex_fails_on_bad_string(self, gen, string):
          match = gen._regex.match(string)
          assert match is None
          
     @staticmethod
     def file_pattern(x):
          return 'data{}.txt'.format(x)