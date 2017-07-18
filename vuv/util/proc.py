import os, uuid
import multiprocess as M
import subprocess as S
from Queue import Queue

def poll(proc, listeners):
     while True:
          line = proc.stdout.readline()
          
          if (line == '') and (proc.poll() is not None):
               return
          else:
               for call in listeners.values():
                    call(line)

class CmdProcess(object):
     
     def proc_init(self):
          '''Implement in subclass. Any pre-process 
          logic that should be performed.
          '''
     
     def __init__(self):
          self._listeners = dict()
          self._call = ''
          
     @property
     def call(self):
          return self._call
     
     @call.getter
     def call(self, value):
          #may want to do some verification logic here at some point
          self._call = value
     
     def __del__(self):
          self.stop()
     
     def start(self):
          '''Start the process. 
          Called in a separate thread. This call is ignored if the process
          is already running.'''
          
          #if process exists and is running, ignore
          if hasattr(self, 'proc'):
               if self.proc.poll() is None:
                    return
          
          self.proc_init()
          
          self.proc = S.Popen(self.call, stdout = S.PIPE)
          
          poll_args = (self.proc, self._listeners)
          self.poll_proc = M.Process(target = poll, args = poll_args)
          
     
     def stop(self):
          '''Stop the process. 
          This call is ignored if the process is stopped.'''
          
          #if process exists and is running, stop
          if hasattr(self, 'proc'):
               if self.proc.poll() is None:
                    call = ['taskkill', 
                            '/F', '/T', '/PID',
                            str(self.proc.pid)]
                    S.call(call)
                    
          if hasattr(self, 'poll_proc'):
               if self.poll_proc.is_alive():
                    self.poll_proc.terminate()
          
     
     def addListener(self, listen_call):
          '''Add listener to process stdout. listen_call should
          be a function which accepts a list of strings as input,
          corresponding to lines from stdout.
          
          addListener returns a LISTEN_ID value which is passed to
          removeListener to stop data being passed from stdout to
          that function.
          '''
          
          #generate a uuid, pull only an 8-bit number
          num = uuid.uuid4().clock_seq_low
          #chances for collision low so easiest method to prevent is
          while self._listeners.has_key(num):
               num = uuid.uuid4().clock_seq_low
          
          self._listeners[num] = listen_call
          return num
     
     def removeListener(self, call_id):
          '''Remove a listener from the process with LISTEN_ID call_id,
          corresponding to the value returned with addListener was called.
          '''
          try:
               self._listeners.pop(call_id)
          except Exception:
               return