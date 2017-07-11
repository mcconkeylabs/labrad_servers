import sys
from PyQt4 import QtGui, uic, QtCore
from basic_scan import ScanWidget

class TestWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        ui_class, ui_widget = uic.loadUiType('stepper_calibration.ui')
        
        self.ui = ui_class()
        self.ui.setupUi(self)
        self.show()
        
    @QtCore.pyqtSlot()
    def on_buttonBox_accepted(self):
        print 'accepted'
        
    @QtCore.pyqtSlot()
    def on_buttonBox_rejected(self):
        print 'rejected'
    

def main():
    app = QtGui.QApplication(sys.argv)
    
    w = TestWidget()
    w.show()
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()