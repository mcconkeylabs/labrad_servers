import sys
import vuv_scan as scan
import labrad.units as U
from PyQt4 import QtCore, QtGui, uic

PULSER_SERVER = 'VUV BNC Serial Server'

class ScannerWindow(QtGui.QMainWindow):
    def __init__(self, cxn):
        QtGui.QMainWindow.__init__(self)
        ui_class, ui_widget = uic.loadUiType('mainWindow.ui')
        self.ui = ui_class()
        self.ui.setupUi(self)
        self.guiInit()
        self.show()
        
        self.cxn = cxn
        self.pulser = cxn[PULSER_SERVER]
        self.pulser.select_device(0)
        
    def guiInit(self):
        self.ui.channels.setValidator(QtGui.QIntValidator(1, 4000))
        self.ui.passes.setValidator(QtGui.QDoubleValidator())
        self.ui.chPerBin.setValidator(QtGui.QDoubleValidator())
        self.ui.dwellTime.setValidator(QtGui.QDoubleValidator())
        
    @QtCore.pyqtSlot()
    def on_scanButton_clicked(self):
        self.readParameters()
        print 'Initializing pulser {0} with {1}'.format(self.pulser, self.dcyc)
        scan.initializePulser(self.pulser, self.dcyc[0], self.dcyc[1])
        for i in range(self.sweeps):
            scan.scanPass(self.pulser, self.advs, self.dwell)
    
    def readParameters(self):
        #duty cycle
        ratio = float(self.ui.chPerBin.text())
        chs = int(ratio * 8)
        self.dcyc = (1, chs - 1)
        
        #dwell time
        dwell = float(self.ui.dwellTime.text())
        self.dwell = U.Value(dwell, 's')

        #pulse advances        
        self.advs = int(self.ui.channels.text()) * 8
        
        #sweeps
        self.sweeps = int(self.ui.passes.text())    
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    
    import sys
    del sys.modules['twisted.internet.reactor']
    
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    import labrad, labrad.util, labrad.types
    cxn = labrad.connect()
    window = ScannerWindow(cxn)
    window.show()
    
    reactor.runReturn()
    sys.exit(app.exec_())