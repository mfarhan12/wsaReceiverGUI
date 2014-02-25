
import sys
import socket
from PySide import QtGui, QtCore
from util import frequency_text
from pyrf.devices.thinkrf import WSA4000

# define constants
MIN_FREQ = 0
MAX_FREQ = 8e9
MHZ = 1e6
CONNECTED_STATE = 'CONNECTED'
DEMO_STATE = 'DEMO'
RFE_MODES = ['ZIF', 'SH', 'HDR']
try:
    from twisted.internet.defer import inlineCallbacks
except ImportError:
    def inlineCallbacks(fn):
        pass

# define the properties of the main window
class MainWindow(QtGui.QMainWindow):
    """
    The main window and menus
    """
    def __init__(self, name=None):
        super(MainWindow, self).__init__()
        self.initUI()
        # connect to the wsa device if the input was provided in console
        self.dut = None
        self._reactor = self._get_reactor()
        if len(sys.argv) > 1:
            self.open_device(sys.argv[1])
        else:
            self.open_device_dialog()
        self.show()

    def _get_reactor(self):
        # late import because installReactor is being used
        from twisted.internet import reactor
        return reactor

    # initialize the the UI
    def initUI(self):
        openAction = QtGui.QAction('&Open Device', self)
        openAction.triggered.connect(self.open_device_dialog)
        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)
        self.setWindowTitle('PyRF Receiver Controller')
        self.state = None
        self.setMaximumHeight(20)
        self.setMaximumWidth(20)
    # connect to device after GUI loaded
    def open_device_dialog(self):

        name, ok = QtGui.QInputDialog.getText(self, 'Open Device',
            'Enter a hostname or IP address:')
        while True:
            
            if not ok and self.state is not None:
                self.setCentralWidget(MainPanel(self.dut,self.state))
                return
                
            if not ok and self.state == DEMO_STATE:
                QtGui.QMessageBox.information(self, 'Connection Error', 
                'Failed to connect to WSA5000, Initiating demo mode')
                self.setWindowTitle('WSA5000 Receiver Controller (Demo Mode)')
                self.setCentralWidget(MainPanel(None,self.state))
                return
            
            self.open_device(name)
            if self.state == DEMO_STATE:
                self.setWindowTitle('WSA5000 Receiver Controller (Demo Mode)')
            elif self.state == CONNECTED_STATE:
                self.setWindowTitle('WSA5000 Receiver Controller')
            self.setCentralWidget(MainPanel(self.dut,self.state))
            return

    # connect to wsa 
    @inlineCallbacks
    def open_device(self, name):
        dut = WSA4000()
        try:
            dut.connect(name)
            if '--reset' in sys.argv:
                yield dut.reset()
            self.dut = dut
            self.state = CONNECTED_STATE
        except socket.error:
                QtGui.QMessageBox.information(self, 'Connection Error', 
                'Failed to connect to WSA5000, Initiating demo mode')
                self.state = DEMO_STATE
        return

    def closeEvent(self, event):
        event.accept()
        self._reactor.stop()

# Panel that contains all the GUI items
class MainPanel(QtGui.QWidget):
    """
    The spectrum view and controls
    """
    def __init__(self, dut, state):
        super(MainPanel, self).__init__()
        self.dut = dut
        self.state = state
        self.center_freq = None
        self.initUI()
        if self.state == CONNECTED_STATE:
            self.dut.reset()
    def initUI(self):
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0,4)
        
        y = 0

        grid.addWidget(self._atten_controls(),y, 1, 1, 1)
        grid.addWidget(QtGui.QLabel('IQ Path:'), y, 2, 1, 1)
        grid.addWidget(self._iq_controls(),y, 3, 1, 1)
        grid.addWidget(QtGui.QLabel('RFE Mode:'),y, 4, 1, 1)
        grid.addWidget(self._rfe_controls(),y, 5, 1, 1)
        y += 1
        freq, steps, freq_plus, freq_minus = self._freq_controls()
        grid.addWidget(QtGui.QLabel('Center Freq:'), y, 1, 1, 1)
        grid.addWidget(freq, y, 2, 1, 2)
        grid.addWidget(QtGui.QLabel('MHz'), y, 4, 1, 1)
        y += 1
        grid.addWidget(steps, y, 2, 1, 2)
        grid.addWidget(freq_minus, y, 1, 1, 1)
        grid.addWidget(freq_plus, y, 4, 1, 1)

        self.setLayout(grid)
        self.show()
    
    def _atten_controls(self):
        atten = QtGui.QCheckBox('Attenuation')
        atten.setChecked(True)
        self._atten = atten
        atten.clicked.connect(lambda: self.update_wsa_settings())
        return atten
    
    def _iq_controls(self):
        iq = QtGui.QComboBox(self)
        iq.addItem("WSA Digitizer")
        iq.addItem("External Digitizer")
        self._iq_box = iq

        iq.currentIndexChanged.connect(lambda: self.update_wsa_settings())
        return iq
        
    def _rfe_controls(self):
        rfe = QtGui.QComboBox(self)
        for mode in RFE_MODES:
            rfe.addItem(mode)

        self._rfe_box = rfe
        rfe.currentIndexChanged.connect(lambda: self.update_wsa_settings())
        return rfe

        

        
    @inlineCallbacks
    def _read_update_freq_edit(self):
        "Get current frequency from self.dut and update the edit box"
        if self.state == CONNECTED_STATE:
            self.center_freq = yield self.dut.freq()
        elif self.state == DEMO_STATE:
            self.center_freq = 2400e6
        self._update_freq_edit()

    def _update_freq_edit(self):
        "Update the frequency edit box from self.center_freq"
        if self.center_freq is None:
            self._freq_edit.setText("---")
        else:
            self._freq_edit.setText("%0.1f" % (self.center_freq / MHZ))

    def _freq_controls(self):
        freq = QtGui.QLineEdit("")
        self._freq_edit = freq
        self._read_update_freq_edit()
        def write_freq():
            try:
                f = float(freq.text())
            except ValueError:
                return

            self.set_freq_mhz(f)
        freq.editingFinished.connect(write_freq)

        steps = QtGui.QComboBox(self)
        steps.addItem("Adjust: 1 MHz")
        steps.addItem("Adjust: 2.5 MHz")
        steps.addItem("Adjust: 10 MHz")
        steps.addItem("Adjust: 25 MHz")
        steps.addItem("Adjust: 100 MHz")
        steps.setCurrentIndex(2)
        def freq_step(factor):
            try:
                f = float(freq.text())
            except ValueError:
                self._update_freq_edit()
                return
            delta = float(steps.currentText().split()[1]) * factor
            freq.setText("%0.1f" % (f + delta))
            write_freq()
        freq_minus = QtGui.QPushButton('-')
        freq_minus.clicked.connect(lambda: freq_step(-1))
        freq_plus = QtGui.QPushButton('+')
        freq_plus.clicked.connect(lambda: freq_step(1))
        return freq, steps, freq_plus, freq_minus
    
    def update_wsa_settings(self):

        if self.state == CONNECTED_STATE:
            if self._atten.checkState() == QtCore.Qt.CheckState.Unchecked:
                self.dut.scpiset(':INPUT:ATTENUATOR 0')
            else:
                self.dut.scpiset(':INPUT:ATTENUATOR 1')
                
            if self._iq_box.currentIndex() == 0:
                self.dut.scpiset('OUTPUT:IQ:MODE DIGITIZER')
            else:
                self.dut.scpiset('OUTPUT:IQ:MODE CONNECTOR')
       
        rfe_mode = self._rfe_box.currentText()
        self.dut.scpiset('INPUT:MODE: ' + rfe_mode)
        
    def set_freq_mhz(self, f):
        center_freq = f * MHZ
        if center_freq > MAX_FREQ or center_freq < MIN_FREQ:          
            self._freq_edit.setText(str((self.center_freq/MHZ)))
            return
            
        self.center_freq = center_freq
        if self.state == CONNECTED_STATE:
            self.dut.freq(self.center_freq)
