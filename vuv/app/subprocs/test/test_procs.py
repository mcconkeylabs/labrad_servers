import pytest
from vuv.app import procs

@pytest.fixture
def srv():
     srv = procs.ProcessWrapper()