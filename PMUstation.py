
#
#  A PMU device can contain multiple PMUs frames.

from PyQt5.QtCore import QThread, pyqtSignal, QDate, QTime, QDateTime
from time import sleep
import datetime
import socket
from ctypes import *
import math

"""
An object to contain the information of a single data frame.
This object is passed as the argument of the onFrameDataReaded
signal to the main thread.
"""
class PMUdataframe(object):
    Nch = 0         # Number of data channels
    dataframe = {}  # Data frame. A dict where the keys are the channel names.
                    # Each key contains the value of the corresponding channel.
    timestamp = type(datetime.datetime)
    fracsec = 0

class PMUstation(QThread):

    idCode = 0
    num_pmu = 0        # Number of PMU devices (data streams) in this PMU station
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
                        #                 3 re-connect socket (without asking configuration frame)
    index = 0           # Index of the PMU station in the list.

    offsets = []
    frame_counter = 0
    phasor_format = 1    # 1: floating point, each value is 4 bytes. 0: 2 bytes integer
    analog_format = 1   # 1: floating point, each value is 4 bytes. 0: 2 bytes integer
    freq_format = 1     # 1: floating point, each value is 4 bytes. 0: 2 bytes integer
    numBytesData = 0    # Number of bytes in the data frame

    frame = PMUdataframe()
    # Message codes: 1 socket connected
    #                2 socket timeout
    #                3 socket re-connected
    #                4 socket disconnected

    # Thread signals:
    onFinished = pyqtSignal(int)                        # Signal finished task and send PMU list index.
    onConfigFrameReaded = pyqtSignal(int)               # Signal a config frame readed and send PMU list index.
    onDataFrameReaded = pyqtSignal(PMUdataframe, int)   # Signal the readed dataframe and PMU list index.
    onMessage = pyqtSignal(int,int)                     # Signal message code and PMU list index.

    def __init__(self, id, ipadr, tcpport, idx, parent = None):
        
        QThread.__init__(self, parent)
        self.idCode = id
        self.tcpport = tcpport
        self.ipaddr = ipadr
        self.index = idx
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.settimeout(5)
        self.phasor_format = 1    # 1: floating point, each value is 4 bytes. 0: 2 bytes integer
        self.analog_format = 1   # 1: floating point, each value is 4 bytes. 0: 2 bytes integer
        self.freq_format = 1     # 1: floating point, each value is 4 bytes. 0: 2 bytes integer

    def run(self):
        if self.command == 1: # Connect socket and read PMU configuration frame

            if self.status == 0:
                # Timeout checking:
                try:
                    self.tcpSocket.connect((self.ipaddr,self.tcpport))
                except socket.timeout:
                    self.tcpSocket.close()
                    self.onMessage.emit(2,self.index) # Message code 2: socket timeout
                    self.command = 0 # Reset command
                    return
                else:
                    self.onMessage.emit(1,self.index) # Message code 1: socket sucessfuly connected
                    self.status = 1      # Status 1: connected
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
                    self.tcpSocket.send(buffer)
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05'
                    self.tcpSocket.send(buffer)

                    read_buffer = bytes(0)
                    to_rcv = 804
                    # Sometimes the socket read does not return all the required bytes.
                    while (to_rcv > 0):
                        read_tmp = self.tcpSocket.recv(to_rcv)
                        to_rcv = to_rcv - len(read_tmp)
                        read_buffer = b"".join([read_buffer,read_tmp]) # Concatenate the bytes object.
                        #if to_rcv > 0:
                        #    print('To receive {0} bytes a'.format(to_rcv))

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
                        
                        # TODO: incorporate this for in the previous one.
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
                        #print('connected')
                        self.onConfigFrameReaded.emit(self.index) # Signal UI
                        self.calculateDataFrameSize()
                        print('PMU {0} data frame has {1} bytes.'.format(self.index,self.numBytesData))
                        # Signal PMU to start sending data frames:
                        buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
                        self.tcpSocket.send(buffer)
                    else:
                        print('PMU{0} received incorrect configuration frame type or version'.format(self.index))
                        self.status = 0      # Status 1: connected
                        self.tcpSocket.close()

        elif self.command == 2: # Disconnect socket
            if self.status == 1:
                self.tcpSocket.close()
                self.onMessage.emit(4,self.index) # Message code 4: socket disconnected
                self.status = 0
        
        elif self.command == 3: # Re-connect socket
            if self.status == 0:
                # Timeout checking:
                self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    self.tcpSocket.connect((self.ipaddr,self.tcpport))
                except socket.timeout:
                    self.tcpSocket.close()
                    self.onMessage.emit(2,self.index) # Message code 2: socket timeout
                    self.command = 0 # Reset command
                    #return
                else:
                    self.onMessage.emit(3,self.index) # Message code 3: socket sucessfuly re-connected
                    self.status = 1      # Status 1: connected
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
                    self.tcpSocket.send(buffer)
                    self.status = 1
        
        self.command = 0 # Reset command
        i = 0
        # Data receiving infinite loop:
        while(self.status == 1):
            sleep(0.01)
            read_buffer = bytes()
            to_rcv = self.numBytesData
            # Sometimes the socket read does not return all the required bytes.
            while (to_rcv > 0):
                read_tmp = self.tcpSocket.recv(to_rcv)
                to_rcv = to_rcv - len(read_tmp)
                read_buffer = b"".join([read_buffer,read_tmp]) # Concatenate the bytes object.
                #if to_rcv > 0:
                #    print('To receive {0} bytes'.format(to_rcv))

            if read_buffer:
                if (read_buffer[0] == 170) and (read_buffer[1] == 1): # Check 0xAA01 (Data frame)
                    #print(read_buffer)
                    frame_size = (read_buffer[2] << 8) + read_buffer[3]
                    self.idCode = (read_buffer[4] << 8) + read_buffer[5]
                    soc = (read_buffer[6] << 24) + (read_buffer[7] << 16) + (read_buffer[8] << 8) + read_buffer[9]
                    fracsec = (read_buffer[10] << 24) + (read_buffer[11] << 16) + (read_buffer[12] << 8) + read_buffer[13]
                    self.fracsec_f = fracsec / 1000000.0
                    self.fracsec_f = float("{:.3f}".format(self.fracsec_f))
                    self.date_time = datetime.datetime.fromtimestamp(soc)  
                    freq_tmp = (read_buffer[40] << 24) + (read_buffer[41] << 16) + (read_buffer[42] << 8) + read_buffer[43]
                    cp = pointer(c_int(freq_tmp))           # make this into a c integer
                    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                    self.freq = fp.contents.value         # dereference the pointer, get the float
                    self.frame.dataframe['freq'] = self.freq
                    self.frame.fracsec = self.fracsec_f
                    self.frame.timestamp = self.date_time
                    k = 0
                    for j in range(0, self.num_pmu):
                        k = self.offsets[j]
                        for i in range(0, self.num_phasors[j]):
                            #print('j: {0} i:{1} k:{2} len:{3} cnt:{4}'.format(j,i,k,len(read_buffer),self.frame_counter))
                            phasor_tmp = (read_buffer[k] << 24) + (read_buffer[k+1] << 16) + (read_buffer[k+2] << 8) + read_buffer[k+3]
                            cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                            fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                            self.frame.dataframe[self.pmu_phasor_names[self.pmu_names[j]][i]] = {'mag':fp.contents.value}
                            # Read phasor
                            phasor_tmp = (read_buffer[k+4] << 24) + (read_buffer[k+5] << 16) + (read_buffer[k+6] << 8) + read_buffer[k+7]
                            cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                            fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                            self.frame.dataframe[self.pmu_phasor_names[self.pmu_names[j]][i]].update({'ang':(fp.contents.value * 180.0) / math.pi})                                                                              
                            k += 8
                    self.frame_counter += 1
                    self.onDataFrameReaded.emit(self.frame,self.index)
            i = i + 1
            if (self.command == 2):
                # Signal the PMU to stop sending data frames:
                buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
                self.tcpSocket.send(buffer)
                self.tcpSocket.close()
                self.onMessage.emit(4,self.index) # Message code 4: socket disconnected
                self.status = 0
                self.command = 0
        
        self.onFinished.emit(self.index)           
    
    def setCommand(self,cmd):
        self.command = cmd
    
    def getStatus(self):
        return self.status

    def updateIp(self, newip):
        self.ipaddr = newip
    
    def updateTcpPort(self, port):
        self.tcpport = port
    
    """ 
    Calculates the size in bytes of the data frame based on
    the information obtained in the header frame.
    """
    def calculateDataFrameSize(self):
        total = 0
        for i in range(0, self.num_pmu):
            if self.phasor_format:
                total = total + self.num_phasors[i] * 8 # Two values per phasor, 4 bytes each.
            else:
                total = total + self.num_phasors[i] * 4
            if self.freq_format:
                total = total + 2 * 4 # Two values (freq and rocof), 4 bytes each.
            else:
                total = total + 2 * 2 
            if self.analog_format:
                total = total + self.num_analogs[i] * 4 # 4 bytes each analog channel.
            else:
                total = total + self.num_analogs[i] * 2
            total = total + self.num_digitals[i] * 2    # 2 bytes per digital channel.
            total = total + 2   # Stat field, 2 bytes

        self.numBytesData = total + 16 # 16 bytes for fixed header and CRC fields.

        



