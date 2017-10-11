import time
from PyQt5 import QtGui, QtWidgets
from QtWidgets import QApplication, QDialog
from ui_scanwindow import Ui_ScanDialog

import config

class BinMultValidator(QtGui.QDoubleValidator):
     def validate(self, lineInput, pos):
          try:
               val = float(lineInput)
          except ValueError:
               return self.Invalid
          
          if (val % config.ADV_PER_CH) == 0.0:
               return self.Acceptable
          else:
               return self.Intermediate

class ScanDialog(QDialog):
     def __init__(self, controller):
          super(ScanDialog, self).__init__()
          
          self.ctrl = controller
          self.scan = config.DEFAULT_SCAN_CONFIG
          
          #set up designer interface
          self.ui = Ui_ScanDialog()
          self.ui.setupUi(self)
          self._ui_init()
          
     def _ui_init(self):
          #start/abort buttons
          self.ui.startButton.clicked.connect(self.start_click)
          self.ui.abortButton.clicked.connect(self.abort_click)
          
          #file settings
          self.ui.saveFileLabel.text = ''
          self.ui.filePatter.text = ''
          self.ui.saveFolder.text = ''
          
          self.ui.saveFolderButton.clicked.connect(self.folder_click)
          
          #pass settings
          self.ui.channels.setValidator(QtGui.QIntValidator())
          self.ui.passes.setValidator(QtGui.QIntValidator())
          self.ui.chPerBin.setValidator(BinMultValidator())
          self.ui.dwellTime.setValidator(QtGui.QDoubleValidator())
          self.ui.scanLengthLabel.text = ''
          
          #update scan time hooks
          for name in ['channels', 'passes', 'dwellTime']:
               field = getattr(self.ui, name)
               field.textChanged.connect(self.update_scan_time_label)
               
     def read_settings(self):
          data = {'channels' : int(self.ui.channels.text),
                  'passes' : int(self.ui.channels),
                  'chPerBin' : float(self.ui.chPerBin.text),
                  'dwellTime' : float(self.ui.dwellTime.text),
                  'saveFolder' : self.ui.saveFolder.text,
                  'savePattern' : self.ui.filePattern.text
                  }
          self.scan = config.ScanConfig._make([data[f] 
                         for f in config.ScanConfig._fields])
          
     #include dummy field for use as callback
     def update_scan_time_label(self, text=''):
          self.read_settings()
          
          seconds = self.channels * self.passes * self.dwell_time
          tv = time.gmtime(seconds)
          
          #subtract one for 1 day offset in day value
          fields = [('d', tv.tm_yday - 1),
                    ('h', tv.tm_hour),
                    ('m', tv.tm_min),
                    ('s', tv.tm_sec)]
          
          #build output string from non-zero time values
          time_str = ''.join(['{0}{1}'.format(v,k) for (k, v) in fields if v != 0])
          self.ui.saveFileLabel.text = time_str
          
     def folder_click(self, clicked=False):
          folderPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                  'Save Data Directory')
          self.ui.saveFolder.text = folderPath
          
     def start_click(self, clicked=False):
          self.read_settings()
          self.ctrl.scan_config = self.scan
          self.ctrl.start()
     
     def abort_click(self, clicked=False):
          self.ctrl.abort()