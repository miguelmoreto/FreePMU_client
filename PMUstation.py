
#
#  A PMU can contain data from multiple units.

from PyQt5.QtCore import QThread, pyqtSignal, QDate, QTime, QDateTime
from time import sleep
import datetime
import socket
from ctypes import *

class PMUstation(QThread):

    idCode = 0
    num_pmus = 0        # Number of PMU devices (data streams) in this PMU station
    num_phasors = []    # Number of phasors in each PMU device
    num_analogs = []    # Number of analog channels in each PMU device
    num_digitals = []   # Number of digital channels in each PMU device
    pmu_names = []      # List with the names of all PMU devices
    pmu_phasor_names = {}       # Dictionary containing a list of phasor names for for each PMU device
    nominal_frequency = 60
    fracsec_f = 0
    tcpport = 0
    ipaddr = ''
    tcpSocket = type(socket.socket())
    status = 0          # Status code: 0 idle, 1 connected
    command = 0         # Command code:   0 does nothing,
                        #                 1 connect socket (send configuration frame)
                        #                 2 disconnect socket 
                        #                 3 re-connect socket (without sending configuration frame)
    index = 0           # Index of the PMU station in a list.

    offsets = []

    # Message codes: 1 socket connected
    #                2 socket timeout
    #                3 socket re-connected
    #                4 socket disconnected

    # Thread signals:
    finished = pyqtSignal(int)
    update = pyqtSignal(int)
    updateTimeFreq = pyqtSignal(datetime.datetime,float,float)
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
        print(type(parent))
        print(parent)

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
                    # Signal PMU to start sending data frames:
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
                    self.tcpSocket.send(buffer)

        elif self.command == 2: # Disconnect socket
            if self.status == 1:
                self.tcpSocket.close()
                self.message.emit(4) # Message code 4: socket disconnected
                self.status = 0
        
        elif self.command == 3: # Re-connect socket
            if self.status == 0:
                # Timeout checking:
                self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.tcpSocket.connect((self.ipaddr,self.tcpport))
                except socket.timeout:
                    self.tcpSocket.close()
                    self.message.emit(2) # Message code 2: socket timeout
                    self.command = 0 # Reset command
                    #return
                else:
                    self.message.emit(3) # Message code 3: socket sucessfuly re-connected
                    self.status = 1      # Status 1: connected
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
                    self.tcpSocket.send(buffer)
                    self.status = 1
        
        self.command = 0 # Reset command
        i = 0
        while(self.status == 1):
            sleep(0.01)
            read_buffer = self.tcpSocket.recv(320)
            if read_buffer:
                if (read_buffer[0] == 170) and (read_buffer[1] == 1):
                    #print(read_buffer)
                    frame_size = (read_buffer[2] << 8) + read_buffer[3]
                    self.idCode = (read_buffer[4] << 8) + read_buffer[5]
                    soc = (read_buffer[6] << 24) + (read_buffer[7] << 16) + (read_buffer[8] << 8) + read_buffer[9]
                    fracsec = (read_buffer[10] << 24) + (read_buffer[11] << 16) + (read_buffer[12] << 8) + read_buffer[13]
                    self.fracsec_f = fracsec / 1000000.0
                    self.fracsec_f = float("{:.3f}".format(self.fracsec_f))
                    self.date_time = datetime.datetime.fromtimestamp(soc)  
                    #print("ID CODE:", self.idCode, "SOC:", self.date_time, "FracSec:", self.fracsec_f)
                    #self.label_time.setText(str(self.date_time))
                    #self.label_frac.setText(str(self.fracsec_f))
                    freq_tmp = (read_buffer[40] << 24) + (read_buffer[41] << 16) + (read_buffer[42] << 8) + read_buffer[43]
                    cp = pointer(c_int(freq_tmp))           # make this into a c integer
                    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                    self.freq = fp.contents.value         # dereference the pointer, get the float
                    self.updateTimeFreq.emit(self.date_time,self.fracsec_f,self.freq)
            #sleep(1)
            self.update.emit(i)
            i = i + 1
            if (self.command == 2):
                # Signal the PMU to stop sending data frames:
                buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
                self.tcpSocket.send(buffer)
                self.tcpSocket.close()
                self.message.emit(4) # Message code 4: socket disconnected
                self.status = 0
                self.command = 0
        
        self.finished.emit(self.index)           
        #for i in range(3):
        #    
        #    self.update.emit(i + 1)
        #self.finished.emit(self.index)

    
    def setCommand(self,cmd):
        self.command = cmd
    
    def getStatus(self):
        return self.status

    def updateIp(self, newip):
        self.ipaddr = newip
    
    def updateTcpPort(self, port):
        self.tcpport = port



