from labrad.client import Client
import labrad

import sys
from PyQt4 import QtGui

class ExperimentRunClient(QtGui.QWidget):
    def __init__(self):
        super(ExperimentRunClient, self).__init__()
        
        self.initUI()
        
    def initUI(self):
        self.resize(250, 150)
        
        self.setWindowTitle('Center')    
        self.show()
    
def main():
 #   cxn = labrad.connect()
    app = QtGui.QApplication(sys.argv)
    ex = ExperimentRunClient()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()