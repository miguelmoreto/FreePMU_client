
#
#  A PMU can contain data from multiple units.

from PyQt5.QtCore import QThread, pyqtSignal
from time import sleep
import socket

class PMUstation(QThread):

    idCode = 0
    num_pmus = 0        # Number of PMU devices in this PMU data
    num_phasors = []    # Number of phasors in each PMU device
    num_analogs = []    # Number of analog channels in each PMU device
    num_digitals = []   # Number of digital channels in each PMU device
    pmu_names = []      # List with the names of all PMU devices
    pmu_phasor_names = {}       # Dictionary containing a list of phasor names for for each PMU device
    nominal_frequency = 60
    tcpport = 0
    ipaddr = ''
    tcpSocket = type(socket.socket())
    status = 0          # Status code: 0 idle, 1 connected
    command = 0         # Command code: 0 does nothing, 1 connect socket
    index = 0           # Index of the PMU station in a list.

    offsets = []

    # Message codes: 1 socket connected, 2 socket timeout, 3 

    # Thread signals:
    finished = pyqtSignal(int)
    update = pyqtSignal(int)
    dataframereaded = pyqtSignal(int)
    message = pyqtSignal(int)

    def __init__(self, id, ipadr, tcpport, idx, parent = None):
        
        QThread.__init__(self, parent)
        
        self.idCode = id
        self.tcpport = tcpport
        self.ipaddr = ipadr
        self.index = idx
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.settimeout(5)

    def run(self):
        if self.command == 1: # Connect socket and read PMU configuration frame

            if self.status == 0:
                # Timeout checking:
                try:
                    self.tcpSocket.connect((self.ipaddr,self.tcpport))
                except socket.timeout:
                    self.tcpSocket.close()
                    self.message.emit(2) # Message code 2: socket timeout
                    self.command = 0 # Reset command
                    return
                else:
                    self.message.emit(1) # Message code 1: socket sucessfuly connected
                    self.status = 1      # Status 1: connected
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
                    self.tcpSocket.send(buffer)
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05'
                    self.tcpSocket.send(buffer)
                    read_buffer = self.tcpSocket.recv(804)
                    if read_buffer[1] == 49:
                        self.num_pmu = (read_buffer[18] << 8) + read_buffer[19]
                        nom_freq = read_buffer[107]
                        if nom_freq == 0:
                            self.nominal_freq = 60
                        else:
                            self.nominal_freq = 50
                        offset = 0
                        self.offsets = []
                        self.offsets.append(16)
                        for i in range(0, self.num_pmu):
                            name = str(read_buffer[(20+offset):(36+offset)], 'UTF-8').strip()
                            #name = name.replace(' ','_')
                            self.pmu_names.append(name)
                            #print(self.pmu_names)
                            self.pmu_phasor_names[name] = [] # Create dictionary key with the PMU name
                            self.num_phasors.append((read_buffer[40+offset] << 8) + read_buffer[41+offset])
                            self.num_analogs.append((read_buffer[42+offset] << 8) + read_buffer[43+offset])
                            self.num_digitals.append((read_buffer[44+offset] << 8) + read_buffer[45+offset])
                            offset = offset + 30 + self.num_phasors[i]*16 + self.num_phasors[i]*4
                            self.offsets.append(10+self.num_phasors[i]*8+self.offsets[i])                                                                        
                        
                        for j in range(0, self.num_pmu):
                            for i in range(0, self.num_phasors[j]):
                                if j == 0:
                                    self.pmu_phasor_names[self.pmu_names[j]].append(str(read_buffer[(46+16*i):(62+16*i)], 'UTF-8').strip())
                                elif j == 1:
                                    self.pmu_phasor_names[self.pmu_names[j]].append(str(read_buffer[(88+self.num_phasors[j-1]*16+16*i):(104+self.num_phasors[j-1]*16+16*i)], 'UTF-8').strip())
                                elif j == 2:
                                    self.pmu_phasor_names[self.pmu_names[j]].append(str(read_buffer[(206+self.num_phasors[j-1]*16+16*i):(222+self.num_phasors[j-1]*16+16*i)], 'UTF-8').strip())
                                elif j == 3:
                                    self.pmu_phasor_names[self.pmu_names[j]].append(str(read_buffer[(436+self.num_phasors[j-1]*16+16*i):(452+self.num_phasors[j-1]*16+16*i)], 'UTF-8').strip())
                        
                        
                        #print(self.pmu_phasor_names)
                    print('connected')
                    self.dataframereaded.emit(self.index) # Signal UI
        elif self.command == 2: # Disconnect socket
            if self.status == 1:
                self.tcpSocket.close()
                self.status = 0
        
        self.command = 0 # Reset command
        
                    
        for i in range(3):
            sleep(1)
            self.update.emit(i + 1)
        self.finished.emit(self.index)

    
    def setCommand(self,cmd):
        self.command = cmd
    
    def getStatus(self):
        return self.status

    def updateIp(self, newip):
        self.ipaddr = newip
    
    def updateTcpPort(self, port):
        self.tcpport = port



