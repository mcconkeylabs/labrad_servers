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
from PyQt4 import uic, QtGui
from PyQt4.QtCore import pyqtSlot

STEPPER_TAG = 'VUV Stepper Server'
SMALL_INC = 1
BIG_INC = 4

INIT_MSG = ("<font color='black'>To calibrate, enter the current channel\n"
            "then press Calibrate.</font>")
            
MID_MSG = ("<font color='green'>Now enter the new channel position\n"
           "then press Calibrate again.</font>")
           
END_MSG = ("<font color='red'>ERROR: The calibration values are invalid."
           "Please try again.</font>")

class CalibrationDialog(QtGui.QDialog):
    def __init__(self, cxn, parent=None):
        QtGui.QDialog.__init__(self, parent)
        
        self.stepper = cxn[STEPPER_TAG]
        self._calibrating = False        
        
        ui_class, widget_class = uic.loadUiType('stepper_calibration.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        self.ui.messageLabel.text = INIT_MSG
        self.show()
        
    def _update(self):
        #wait until the stepper stops moving and then update
        state = self.stepper.state()
        while state:
            state = self.stepper.state()
            
        ch, frac = self.stepper.get_position()
        chFloat = ch + (frac / 8.0)
        self.ui.positionInput.text = str(chFloat)
        
    def _advance(self, fracs, direction):
        self.stepper.advance(0, fracs, direction, True, wait=False)
        
    def _startCalibration(self):
        self._calFirst = int(self.ui.positionInput.text)
        self.stepper.advance(1, 0, True, True)
        
        self._calibrating = True
        self.ui.messageLabel.text = MID_MSG
        
    def _endCalibration(self):
        self._calSecond = int(self.ui.positionInput.text)
        calDiff = self._calSecond - self._calFirst
        
        #if previously moving backward, position should not change
        if calDiff in [0, 1]:
            self.stepper.set_position(self._calSecond, 0, 'Forward', wait=False)
            msg = ''
        else:
            msg = END_MSG
                   
        self.ui.messageLabel.text = msg
        self._calibrating = False
    
    @pyqtSlot()
    def on_bigBackButton_clicked(self):
        self._advance(BIG_INC, False)
        self._update()
        
    @pyqtSlot()
    def on_backButton_clicked(self):
        self._advance(SMALL_INC, False)
        self._update()
        
    @pyqtSlot()
    def on_forwardButton_clicked(self):
        self._advance(SMALL_INC, True)
        self._update()
        
    @pyqtSlot()
    def on_bigForwardButton_clicked(self):
        self._advance(BIG_INC, True)
        self._update()
        
    @pyqtSlot()
    def on_calibrateButton_clicked(self):
        if not self._calibrating:
            self._startCalibration()
        else:
            self._endCalibration()
            
    @pyqtSlot()
    def on_buttonBox_accepted(self):
        ch = int(self.ui.positionInput.text)
        self.stepper.set_position(ch, 0)
    
if __name__ == '__main__':
    with labrad.connect() as cxn:
        app = QtGui.QApplication(sys.argv)
        window = CalibrationDialog(cxn)
        sys.exit(app.exec_())