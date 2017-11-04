import PyQt5
from PyQt5 import uic, QtWidgets

class LogWidget(QtWidgets.QWidget):
    
    def __init__(self, procs = []):
        super(LogWidget, self).__init__()
        
        ui_class, ui_widget = uic.loadUiType('logWidget.ui')
        self.ui = ui_class()
        self.ui.setupUi()
        
        self._ui_init(procs)
        self.show()
        
    def _ui_init(self, procs):
        counter = 0
        self.ui.tabWidget.clear()
        
        for p in procs:
            if hasattr(p, 'name'):
                name = p.name
            else:
                name = 'Process {}'.format(counter)
                counter += 1
            
            view = LogViewWidget()
            view.append_line.connect(p.outputAvailable)
            
            self.ui.tabWidget.addTab(view, name)
                
            
class LogViewWidget(QtWidgets.QWidget):
    
    def __init__(self):
        super(LogViewWidget, self).__init__()
        
        ui_class, ui_widget = uic.loadUiType('logViewWidget.ui')
        self.ui = ui_class()
        self.ui.setupUi()
        
    def _ui_init(self):
        self.ui.setReadOnly(True)
        self.ui.plainText(True)
        
        self.ui.textEdit.setAlignment(PyQt5.QtCore.Qt.AlignLeft)
        
    def append_line(self, line):
        self.ui.textEdit.append(line)
        
        maxval = self.ui.textEdit.verticalScrollBar.maximum()
        self.ui.textEdit.verticalScrollBar.setValue(maxval)