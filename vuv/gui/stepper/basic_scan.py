# Copyright (C) 2016  Jeffery Dech
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import labrad, sys
import labrad.units as U
from PyQt4 import uic, QtGui
from PyQt4.QtCore import pyqtSlot
from stepper_calibration import CalibrationDialog

SCANNER_TAG = 'Scan Server'
MCS_TAG = 'Ortec MCS Server'
SMALL_INC = 1
BIG_INC = 4

class ScanWidget(QtGui.QWidget):
    
    def __init__(self, cxn, parent=None):
        QtGui.QWidget.__init__(self)
        
        self._reg = cxn.registry        
        
        ui_class, widget_class = uic.loadUiType('basic_scan.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        self._initGui()
        self.show()
        
        self.scanner = cxn[SCANNER_TAG]
        self.mcs = cxn[MCS_TAG]
        
    def _initGui(self):
        self.ui.messageLabel.text = ''
        
        sret = self.scanner.packet()\
                   .scan_range(key='range')\
                   .dwell()\
                   .channels_per_bin(key='cpb')\
                   .send()
        
        start, stop = sret['range']
        
        #initial values
        self.ui.startInput.text = str(start)
        self.ui.endInput.text = str(stop)
        self.ui.dwellInput.text = str(sret['dwell']['s'])
        self.ui.binInput.text = str(sret['cpb'])
        self.ui.messageLabel.text = ''
    
        #validators
        self.ui.startInput.setValidator(QtGui.QIntValidator(self))
        self.ui.endInput.setValidator(QtGui.QIntValidator(self))
        self.ui.dwellInput.setValidator(QtGui.QDoubleValidator(self))
        self.ui.binInput.setValidator(QtGui.QDoubleValidator(self))
        
    def _setupScan(self):
        start = int(self.ui.startInput.text)
        stop = int(self.ui.stopInput.text)
        dwell = float(self.ui.dwellInput.text)
        cPerBin = float(self.ui.binInput.text)
        
        self.scanner.packet()\
            .scan_range(start, stop)\
            .dwell(U.Value(dwell, 's'))\
            .channels_per_bin(cPerBin)\
            .send()
        
        
    @pyqtSlot()
    def on_calibrateButton_clicked(self):
        calibrateDialog = CalibrationDialog(cxn, self)
        calibrateDialog.show()
        
    @pyqtSlot()
    def on_saveButton_clicked(self):
        current = self.ui.saveInput.text
        filePath = QtGui.QFileDialog.getOpenFileName(parent = self,
                                                     selectedFilter='*.mcs',
                                                     directory = current)
        self.ui.saveInput.text = filePath
        self.mcs.save_directory(filePath)
        
    @pyqtSlot()
    def on_startButton_clicked(self):
        self._setupScan()
        self.scanner.start()
    
    @pyqtSlot()
    def on_stopButton_clicked(self):
        self.scanner.stop()
    
if __name__ == '__main__':
    with labrad.connect() as cxn:
        app = QtGui.QApplication(sys.argv)
        window = CalibrationDialog(cxn)
        sys.exit(app.exec_())