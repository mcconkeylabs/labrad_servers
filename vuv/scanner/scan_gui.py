import time, sys
import os.path
import labrad.units as U
from PyQt5 import QtGui, uic, QtWidgets

import configuration
import controller

FILE_SUFFIX = ".dat"

class BinMultValidator(QtGui.QDoubleValidator):
     def validate(self, lineInput, pos):
          try:
               val = float(lineInput)
          except ValueError:
               return self.Invalid
          
          if (val % configuration.ADV_PER_CH) == 0.0:
               return self.Acceptable
          else:
               return self.Intermediate

class ScanDialog(QtWidgets.QDialog):
     def __init__(self, controller):
          super(ScanDialog, self).__init__()
          
          self.ctrl = controller
          self.scan = configuration.DEFAULT_SCAN_CONFIG
          
          #set up designer interface
          ui_class, ui_widget = uic.loadUiType('scanwindow.ui')
          self.ui = ui_class()
          self.ui.setupUi(self)
          self._ui_init()
          self.show()
          
     def _ui_init(self):
          #start/abort buttons
          self.ui.startButton.clicked.connect(self.start_click)
          self.ui.abortButton.clicked.connect(self.abort_click)
          
          #file settings
          self.ui.saveFileLabel.setText('')
          self.ui.filePattern.setText('')
          self.ui.saveFolder.setText('')
          
          self.ui.saveFolderButton.clicked.connect(self.folder_click)
          self.ui.filePattern.textChanged.connect(self.refresh_scan_pattern)
          
          #pass settings
          self.ui.channels.setValidator(QtGui.QIntValidator())
          self.ui.passes.setValidator(QtGui.QIntValidator())
#          self.ui.chPerBin.setValidator(BinMultValidator())
          self.ui.dwellTime.setValidator(QtGui.QDoubleValidator())
          self.ui.scanLengthLabel.setText('')
          
          
          #update scan time hooks
          for name in ['channels', 'passes', 'dwellTime', 'chPerBin']:
               field = getattr(self.ui, name)
               
               field.setText(str(configuration.DEFUALT_GUI[name]))
               field.editingFinished.connect(self.update_scan_time_label)
               
     def read_settings(self):
          data = {'channels' : int(self.ui.channels.text()),
                  'passes' : int(self.ui.passes.text()),
                  'chPerBin' : float(self.ui.chPerBin.text()),
                  'dwellTime' : U.Value(float(self.ui.dwellTime.text()), 's'),
                  'saveFolder' : self.ui.saveFolder.text(),
                  'savePattern' : self.ui.filePattern.text(),
                  'moveOnly' : False,
                  }
          self.scan = configuration.ScanConfig._make([data[f] 
                         for f in configuration.ScanConfig._fields])
          
     #include dummy field for use as callback
     def update_scan_time_label(self, text=''):
          self.read_settings()
          
          seconds = self.scan.channels * self.scan.passes * self.scan.dwellTime['s']
          tv = time.gmtime(seconds)
          
          #subtract one for 1 day offset in day value
          fields = [('d', tv.tm_yday - 1),
                    ('h', tv.tm_hour),
                    ('m', tv.tm_min),
                    ('s', tv.tm_sec)]
          
          #build output string from non-zero time values
          time_str = ''.join(['{0}{1}'.format(v,k) for (k, v) in fields if v != 0])
          self.ui.scanLengthLabel.setText(time_str)
          
     def folder_click(self, clicked=False):
          folderPath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                  'Save Data Directory')
          self.ui.saveFolder.setText(folderPath)
          self.refresh_scan_pattern()
          
     def refresh_scan_pattern(self, text=""):
         fldr = self.ui.saveFolder.text()
         pat = self.ui.filePattern.text()
         
         file_name = pat + '1.mcs'
         path = os.path.join(fldr, file_name)
         normed = os.path.abspath(path)
         
         self.ui.saveFileLabel.setText(normed)
          
          
     def start_click(self, clicked=False):
          self.read_settings()
          self.ctrl.scan_config = self.scan
          self.ctrl.start()
     
     def abort_click(self, clicked=False):
          self.ctrl.abort()
          
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    
    import sys
    del sys.modules['twisted.internet.reactor']
    
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    import labrad, labrad.util, labrad.types
    cxn = labrad.connect()
    ctrl = controller.LabradController(cxn)
    window = ScanDialog(ctrl)
    window.show()
    
    reactor.runReturn()
    sys.exit(app.exec_())