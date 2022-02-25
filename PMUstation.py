
#
#  A PMU can contain data from multiple units.

from PyQt5.QtCore import QThread, pyqtSignal
from time import sleep
import socket

class PMUstation(QThread):
    station_name = ''
    idCode = 0
    num_pmus = 0        # Number of PMU devices in this PMU data
    num_phasors = []    # Number of phasors in each PMU device
    num_analogs = []    # Number of analog channels in each PMU device
    num_digitals = []   # Number of digital channels in each PMU device
    pmu_names = []      # List with the names of all PMU devices
    pmu_phasor_names = {}       # Dictionary containing a list of phasor names for for each PMU device
    tcpport = 0
    ipaddr = ''
    tcpSocket = type(socket.socket())

    # Thread signals:
    finished = pyqtSignal()
    update = pyqtSignal(int)

    def __init__(self, name, id, numpmus, ipadr, tcpport,parent = None):
        
        QThread.__init__(self, parent)
        # TEMP INIT
        self.station_name = name
        self.num_pmus = numpmus
        # TEMP END
        
        self.idCode = id
        self.tcpport = tcpport
        self.ipaddr = ipadr
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.settimeout(5)

    def run(self):
        for i in range(15):
            sleep(1)
            self.update.emit(i + 1)
        self.finished.emit()
    
    def connect(self):
        # Connect to the PMU and retreive the configuration frame.
        # TEMP INIT
        self.pmu_names = [self.station_name + 'a', self.station_name + 'b', self.station_name + 'c']

        for n in self.pmu_names:
            self.pmu_phasor_names[n] = []
            for i in range(3):
                self.pmu_phasor_names[n].append(n + '_ch_'+repr(i))
        # TEMP END

    # DEPRECATED INIT
    def addPMU(self, name = 'default_name', num_p = 0, num_a = 0, num_d = 0):

        self.pmu_phasor_names[name] = []
        self.num_phasors.append(num_p)
        self.num_analogs.append(num_a)
        self.num_digitals.append(num_d)
        self.num_pmus = self.num_pmus + 1

    def addPhasorNames(self, pmuname = '', channelname = ''):

        if (pmuname in self.pmu_phasor_names):
            self.pmu_phasor_names[pmuname].append(channelname)
        else:
            print('ERROR: try to add phasors in a inexistent PMU')
    # DEPRECATED END

    def updateIp(self, newip):
        self.ipaddr = newip
    
    def updateTcpPort(self, port):
        self.tcpport = port



