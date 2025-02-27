import sys
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QTreeWidgetItem
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, uic, QtGui
from pyqtgraph import PlotWidget
import pyqtgraph as pg

#from PySide6 import QtCore
from PyQt5 import QtCore
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt

from ctypes import cdll, c_long, c_int, c_char_p, create_string_buffer

import numpy as np

import time
import struct
import socket
import math
import collections

from ctypes import *
import datetime  

import PMUstation as pmu

class MainWindow(QMainWindow):

    pmus_list = []  # List of PMUstation objects
    pmus_names = [] # PMUs numbered names to show in the combobox

    data_to_plot = {}

    connected = 0
    pressed = 0
    counter = 0
    idx = 0.0

    d_t = 0
    selected_to_plotRT = [] # List of the selected channel names do plot in Real-time

    deque_dict_freq = {}    # Dictionary of deques to store the real time frequency values to plot.
    #deque_dict_mag = {}     # Dictionary of deques to store the real time magnitude values to plot.
    #deque_dict_angle = {}   # Dictionary of deques to store the real time angles values to plot.
    #data_lines_mag = {}     # Dictionary of pyqtgraph lineplots.
    deque_time = collections.deque()

    overflow = False
    graph_data_y0 = []
    graph_data_y1 = []
    graph_data_y2 = []
    graph_data_y3 = []
    graph_data_y4 = []
    graph_data_y5 = []
    graph_data_y6 = []
    graph_data_y7 = []
    graph_data_y8 = []
    graph_data_y9 = []
    graph_data_y10 = []
    graph_data_x = []

    data_line0 = 0
    data_line1 = 0
    data_line2 = 0
    data_line3 = 0
    data_line4 = 0
    data_line5 = 0
    data_line6 = 0
    data_line7 = 0
    data_line8 = 0
    data_line9 = 0
    data_line10 = 0

    station_name = []
    num_phasors = []
    num_analogs = []
    num_digitals = []
    offsets = []

    phasor_name0 = []
    phasor_name1 = []
    phasor_name2 = []
    phasor_name3 = []

    phasors_mag0 = []
    phasors_phase0 = []

    phasors_mag1 = []
    phasors_phase1 = []

    phasors_mag2 = []
    phasors_phase2 = []

    phasors_mag3 = []
    phasors_phase3 = []

    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi('freepmu_pdc.ui', self)
        #self.pushButton_connect.clicked.connect(self.on_pushButton_connect_clicked)
        #self.comboBox.currentIndexChanged.connect(self.on_comboBox_clicked)
        self.deque_time = collections.deque(maxlen=300)

        self.pen0 = pg.mkPen(color=(255, 0, 0))

        self.timer1 = QtCore.QTimer()
        self.timer1.timeout.connect(self.showTime)

        self.graph_freq.setLabel('left', "<span style=\"color:blue;font-size:12px\">Frequency (Hz)</span>")
        self.graph_freq.setLabel('bottom', "<span style=\"color:blue;font-size:12px\">Time (s)</span>")
        self.graph_freq.setBackground('w')
        self.plotWidgetMag.setBackground('w')
        self.plotWidgetMag.setLabel('left','Magnitude [V]')
        self.plotWidgetMag.setXRange(0.0,10,padding = 0.02)
        self.plotWidgetMag.setYRange(0.0,230,padding = 0.02)
        self.plotWidgetMag.showGrid(x=True,y=True)
        self.plotWidgetPhase.setBackground('w')
        self.plotWidgetPhase.setLabel('left','Phase [°]')
        self.plotWidgetPhase.setXRange(0.0,10,padding = 0.02)
        self.plotWidgetPhase.setYRange(-190,190,padding = 0.02)
        self.plotWidgetPhase.showGrid(x=True,y=True)
        self.plotWidgetFreq.setBackground('w')
        self.plotWidgetFreq.setLabel('left','Freq. [Hz]')
        self.plotWidgetFreq.setXRange(0.0,10.0,padding = 0.02)
        self.plotWidgetFreq.setYRange(50.0,65.0,padding = 0.02)
        self.plotWidgetFreq.showGrid(x=True,y=True)
        self.graph_freq.setXRange(0.0, 10.0, padding=0)

        self.graph_mag.setLabel('left', "<span style=\"color:blue;font-size:12px\">Magnitude (V)</span>")
        self.graph_mag.setLabel('bottom', "<span style=\"color:blue;font-size:12px\">Time (s)</span>")
        self.graph_mag.setBackground('w')
        self.graph_mag.setYRange(200.0, 230.0, padding=0)
        self.graph_mag.setXRange(0.0, 10.0, padding=0)

        # Formatting the treeWidget
        self.treeWidgetPMU.setColumnWidth(0, 150)
        self.treeWidgetPMU.setColumnWidth(1, 20)
        self.treeWidgetPMU.setColumnWidth(2, 20)

        self.btnAddPMU.clicked.connect(self.onBtnAddPMUclicked)
        self.btnRemovePMU.clicked.connect(self.onbtnRemovePMUclicked)
        self.btnDisconnect.clicked.connect(self.onBtnDisconnectClicked)
        self.treeWidgetPMU.itemChanged.connect(self.onTreeWidgetChange)


    def onTreeWidgetChange(self,item,column):

        chName = item.text(0)
        parent = item.parent()
        parent = parent.parent()
        if column == 1: # plot checkbox changed
            status = item.checkState(column)
            if (status == QtCore.Qt.Checked):
                print('Channel {0} Plot status ON'.format(chName))
                self.selected_to_plotRT.append(chName)
                #self.deque_dict_mag[str(parent.text(0))][chName] = collections.deque(maxlen=300)
                #self.data_lines_mag[str(parent.text(0))][chName] = []
                self.counter = 0
            else:
                print('Channel {0} Plot status OFF'.format(chName))
                #del self.deque_dict_mag[str(parent.text(0))][chName]
                #del self.data_lines_mag[str(parent.text(0))][chName]
                self.selected_to_plotRT.remove(chName)
                
        elif column == 2: # export checkbox changed
            status = item.checkState(column)
            if (status == QtCore.Qt.Checked):
                print('Channel {0} Export status ON'.format(chName))
            else:
                print('Channel {0} Export status OFF'.format(chName))
        
        


    """
    Remove a PMU from the list, stop and delete the corresponding thread.
    """
    def onbtnRemovePMUclicked(self):
        itemtext = self.comboPMUs.currentText()
        index = self.comboPMUs.currentIndex()
        total = self.treeWidgetPMU.topLevelItemCount()
        icon = QtGui.QIcon()
        if itemtext: # Do something only if exists at least one item in the combobox
            if self.pmus_list[index].getStatus() == 1:
                self.pmus_list[index].setCommand(2) # Command to disconnect the socket.
                icon.addPixmap(QtGui.QPixmap("images/link.png"),QtGui.QIcon.Normal, QtGui.QIcon.Off)
                self.btnDisconnect.setIcon(icon)
                self.btnDisconnect.setEnabled(False)
                print('{0} socket closed!'.format(self.pmus_names[index]))
                time.sleep(0.1)
                self.pmus_list[index].terminate()
            self.treeWidgetPMU.takeTopLevelItem(index)
            self.comboPMUs.removeItem(index)
            self.comboPMUs.setCurrentIndex(index-1)
            del self.pmus_list[index]
            del self.deque_dict_freq['PMU{0}freq'.format(index)] # Remove de deque object
            #del self.data_lines_mag['PMU{0}'.format(index)]
            #del self.deque_dict_mag['PMU{0}'.format(index)] 
        
            if total == 1: # if it is the last item, disable the button.
                self.btnRemovePMU.setEnabled(False)
                self.labelCurPMUname.setText('PMUx')
                self.labelTimeStamp.setText('--/--/---- --:--')
                self.labelFreqValue.setText('--.----- Hz')
                self.comboPMUs.setCurrentIndex(0)
        
    """
    Add a PMU to the list with the paremeter set in the UI and 
    starts its thread
    """
    def onBtnAddPMUclicked(self):
        ip = str(self.lineEditIp.text())
        port = int(self.lineEditPort.text())
        id = int(self.lineEditPmuId.text())
        index = len(self.pmus_list)
        print(index)
        pmu1 = pmu.PMUstation(id,ip,port, index)
        self.pmus_list.append(pmu1)
        self.pmus_names.append('PMU '+ repr(index))
        
        # Check for connection errors:
        
        self.pmus_list[index].onFinished.connect(self.onTaskFinished)
        self.pmus_list[index].onMessage.connect(self.onTaskMessage)
        self.pmus_list[index].onConfigFrameReaded.connect(self.onTaskConfigFrameReaded)
        self.pmus_list[index].onDataFrameReaded.connect(self.onTaskDataFrameReaded)

        self.pmus_list[index].setCommand(1) # Command to connect the socket.

        self.pmus_list[index].start()
        #self.pmu1.start()
    
    def onBtnDisconnectClicked(self):
        index = self.comboPMUs.currentIndex()
        icon = QtGui.QIcon()
        if self.pmus_list[index].getStatus() == 1:
            self.pmus_list[index].setCommand(2) # Command to disconnect the socket.
            #self.pmus_list[-1].start()
            icon.addPixmap(QtGui.QPixmap("images/link.png"),QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.btnDisconnect.setIcon(icon)   
            print('{0} socket closed!'.format(self.pmus_names[index]))
            #self.btnDisconnect.setEnabled(False)
        elif self.pmus_list[index].getStatus() == 0:
            self.pmus_list[index].setCommand(3) # Command to re-connect the socket.
            self.pmus_list[index].start()
            icon.addPixmap(QtGui.QPixmap("images/broken-link.png"),QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.btnDisconnect.setIcon(icon)

    def onTaskDataFrameReaded(self, frame, idx):
        try:
            # If the dict key does not exist, then this PMU has been removed, so does nothing.
            self.deque_dict_freq['PMU{0}freq'.format(idx)].append(frame.dataframe['freq'])
        except KeyError:
            return

        tempstr = "{0}.{1:04d}".format(time.strftime('%d/%m/%Y %H:%M:%S'),int(frame.fracsec*10000))
        #self.labelTimeStamp.setText(time.strftime('%d/%m/%Y %H:%M:%S.')+repr(fracsec))
        self.labelTimeStamp.setText(tempstr)
        self.labelFreqValue.setText('{0:.5f} Hz'.format(frame.dataframe['freq']))
        self.deque_time.append(self.d_t)
        for chName in self.selected_to_plotRT:
            #self.deque_dict_mag['PMU{0}'.format(idx)][chName].append(frame.dataframe[chName]['mag']) # Add data to the corresponding deque
            #if self.counter == 0:
            #    self.data_lines_mag['PMU{0}'.format(idx)][chName] = self.graph_mag.plot(self.deque_time)
            #print(frame.dataframe[chName])
            pass
        # ideia... criar as deques na thread e inicializar com zero.
        # Aqui na UI, só criar instancias do plotitem ao selecionar.
        

        if self.data_line0 == 0:
            #self.data_line0 = self.graph_freq.plot(self.deque_time, self.deque_dict_freq['PMU{0}freq'.format(idx)], connect="finite", pen=self.pen0)
            self.data_line0 = self.graph_freq.plot(self.pmus_list[idx].plotdata_time, self.pmus_list[idx].plotdata_freq, connect="finite", pen=self.pen0)
            
        else:
            if (self.counter > 300):
                self.graph_freq.setXRange(self.pmus_list[idx].plotdata_time[0], self.pmus_list[idx].plotdata_time[-1], padding=0)
            self.data_line0.setData(self.pmus_list[idx].plotdata_time, self.pmus_list[idx].plotdata_freq, connect='finite', antialias=True)  # Update the data.        
        self.d_t += 0.03333
        self.counter += 1

    def onTaskFinished(self,idx):
        print('{0} task finished.'.format(self.pmus_names[idx]))
    
    def onTaskMessage(self,code,idx):
        
        if code == 1:
            self.statusBar().setStyleSheet("color : green; font: bold 14px")
            self.statusBar().showMessage('{0} connection sucessful!'.format(self.pmus_names[idx]),5000)
            #self.btnDisconnect.setEnabled(True)
        elif code == 2:
            self.statusBar().setStyleSheet("color : red; font: bold 14px")
            self.statusBar().showMessage('{0} socket timeout!'.format(self.pmus_names[idx]),5000)
        elif code == 3:
            self.statusBar().setStyleSheet("color : green; font: bold 14px")
            self.statusBar().showMessage('{0} re-connection sucessful!'.format(self.pmus_names[idx]),5000)
        elif code == 4:
            self.statusBar().setStyleSheet("color : orange; font: bold 14px")
            self.statusBar().showMessage('{0} disconnected!'.format(self.pmus_names[idx]),5000)

    
    def onTaskConfigFrameReaded(self,index):
        self.treeWidgetPMU.itemChanged.disconnect() # to avoid executing the callback at this time
        mainiten = QTreeWidgetItem(self.treeWidgetPMU)
        mainiten.setText(0,self.pmus_names[index])
        # Updating the treeWidget:
        for n in self.pmus_list[index].pmu_names:
            #self.treeWidgetPMU.
            item = QTreeWidgetItem(mainiten)
            item.setText(0,n)
            item.setText(3,'Connected')
            for ch in self.pmus_list[index].pmu_phasor_names[n]:
                subitem = QTreeWidgetItem(item)
                subitem.setText(0,ch)
                subitem.setCheckState(1,False)
                subitem.setCheckState(2,False)
        self.comboPMUs.addItem(self.pmus_names[index])
        #self.comboPMUs.setCurrentIndex(len(self.pmus_names)-1)
        self.labelCurPMUname.setText(self.pmus_names[index])
        self.treeWidgetPMU.expandAll()
        self.btnDisconnect.setEnabled(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("images/broken-link.png"),QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnDisconnect.setIcon(icon)
        self.btnRemovePMU.setEnabled(True)
        # Add deque object to real time plot:
        self.deque_dict_freq['PMU{0}freq'.format(index)]=collections.deque(maxlen=300)
        #self.deque_dict_mag['PMU{0}'.format(index)] = {} # A dict of dicts the will contains a deque for each channel to plot.
        #self.data_lines_mag['PMU{0}'.format(index)] = {}
        self.deque_time.clear()
        self.d_t = 0
        self.counter = 0
        self.treeWidgetPMU.itemChanged.connect(self.onTreeWidgetChange)

    def showTime(self):
        self.pressed = 0
        if self.connected == 1:
            read_buffer = self.tcpCliSock.recv(320)
            if read_buffer:
                if (read_buffer[0] == 170) and (read_buffer[1] == 1):
                    #print(read_buffer)
                    frame_size = (read_buffer[2] << 8) + read_buffer[3]
                    self.id_code = (read_buffer[4] << 8) + read_buffer[5]
                    soc = (read_buffer[6] << 24) + (read_buffer[7] << 16) + (read_buffer[8] << 8) + read_buffer[9]
                    fracsec = (read_buffer[10] << 24) + (read_buffer[11] << 16) + (read_buffer[12] << 8) + read_buffer[13]
                    self.fracsec_f = fracsec / 1000000.0
                    self.fracsec_f = float("{:.3f}".format(self.fracsec_f))
                    self.date_time = datetime.datetime.fromtimestamp(soc)  
                    #print("ID CODE:", self.id_code, "SOC:", self.date_time, "FracSec:", self.fracsec_f)
                    self.label_time.setText(str(self.date_time))
                    self.label_frac.setText(str(self.fracsec_f))
                    freq_tmp = (read_buffer[40] << 24) + (read_buffer[41] << 16) + (read_buffer[42] << 8) + read_buffer[43]
                    cp = pointer(c_int(freq_tmp))           # make this into a c integer
                    fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                    self.freq = fp.contents.value         # dereference the pointer, get the float

                    k = 0
                    for j in range(0, self.num_pmu):
                        k = self.offsets[j]
                        #print(k)
                        for i in range(0, self.num_phasors[j]):
                            if j == 0:
                                phasor_tmp = (read_buffer[k] << 24) + (read_buffer[k+1] << 16) + (read_buffer[k+2] << 8) + read_buffer[k+3]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_mag0[i] = fp.contents.value         # dereference the pointer, get the float
                                #print('Mag0_'+repr(i)+':'+repr(self.phasors_mag0[i]))

                                phasor_tmp = (read_buffer[k+4] << 24) + (read_buffer[k+5] << 16) + (read_buffer[k+6] << 8) + read_buffer[k+7]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_phase0[i] = (fp.contents.value * 180.0) / math.pi        # dereference the pointer, get the float
                                #print('Ang0_'+repr(i)+':'+ repr(self.phasors_phase0[i]))
                            elif j == 1:
                                phasor_tmp = (read_buffer[k] << 24) + (read_buffer[k+1] << 16) + (read_buffer[k+2] << 8) + read_buffer[k+3]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_mag1[i] = fp.contents.value         # dereference the pointer, get the float
                                #print(self.phasors_mag1[i])
                                #print('Mag1_'+repr(i)+':'+ repr(self.phasors_mag1[i]))

                                phasor_tmp = (read_buffer[k+4] << 24) + (read_buffer[k+5] << 16) + (read_buffer[k+6] << 8) + read_buffer[k+7]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_phase1[i] = (fp.contents.value * 180.0) / math.pi        # dereference the pointer, get the float
                                #print(self.phasors_phase1[i])
                                #print('Ang1_'+repr(i)+':'+ repr(self.phasors_phase1[i]))
                            elif j == 2:
                                phasor_tmp = (read_buffer[k] << 24) + (read_buffer[k+1] << 16) + (read_buffer[k+2] << 8) + read_buffer[k+3]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_mag2[i] = fp.contents.value         # dereference the pointer, get the float
                                #print(self.phasors_mag2[i])
                                #print('Mag2_'+repr(i)+':'+ repr(self.phasors_mag2[i]))

                                phasor_tmp = (read_buffer[k+4] << 24) + (read_buffer[k+5] << 16) + (read_buffer[k+6] << 8) + read_buffer[k+7]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_phase2[i] = (fp.contents.value * 180.0) / math.pi        # dereference the pointer, get the float
                                #print(self.phasors_phase2[i])
                                #print('Ang2_'+repr(i)+':'+ repr(self.phasors_phase2[i]))
                            elif j == 3:
                                phasor_tmp = (read_buffer[k] << 24) + (read_buffer[k+1] << 16) + (read_buffer[k+2] << 8) + read_buffer[k+3]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_mag3[i] = fp.contents.value         # dereference the pointer, get the float
                                #print(self.phasors_mag3[i])
                                #print('Mag3_'+repr(i)+':'+ repr(self.phasors_mag3[i]))

                                phasor_tmp = (read_buffer[k+4] << 24) + (read_buffer[k+5] << 16) + (read_buffer[k+6] << 8) + read_buffer[k+7]
                                cp = pointer(c_int(phasor_tmp))           # make this into a c integer
                                fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
                                self.phasors_phase3[i] = (fp.contents.value * 180.0) / math.pi        # dereference the pointer, get the float
                                #print(self.phasors_phase3[i])
                                #print('Ang3_'+repr(i)+':'+ repr(self.phasors_phase3[i]))
                            k += 8


                    # Selecionar pelo combo
                    self.label_freq.setText(str(self.freq))
                    self.label_angle.setText(str(self.phasors_phase0[0]))
                    self.label_mag.setText(str(self.phasors_mag0[0]))

                    if (self.counter > 300):
                        self.overflow = True

                    if self.overflow == True:
                            self.graph_data_x = self.graph_data_x[1:]  # Remove the first y element.
                            self.graph_data_x.append(self.idx)  # Add a new value 1 higher than the last.

                            self.graph_freq.setXRange(self.idx-10.0, self.idx, padding=0)
                            self.graph_phase.setXRange(self.idx-10.0, self.idx, padding=0)

                            self.graph_data_y0 = self.graph_data_y0[1:]  # Remove the first
                            self.graph_data_y0.append(self.freq)  # Add a new random value.

                            self.graph_data_y1 = self.graph_data_y1[1:]  # Remove the first
                            self.graph_data_y1.append(self.mag0[0])  # Add a new random value.

                            self.graph_data_y2 = self.graph_data_y2[1:]  # Remove the first
                            self.graph_data_y2.append(self.mag0[1])  # Add a new random value.

                            self.graph_data_y3 = self.graph_data_y3[1:]  # Remove the first
                            self.graph_data_y3.append(self.mag0[2])  # Add a new random value.

                            #self.graph_data_x.insert(self.counter, self.idx)
                            #self.graph_data_y0.insert(self.counter, self.freq)
                            self.data_line0.setData(self.graph_data_x, self.graph_data_y0, connect="finite")  # Update the data.
                            self.data_line1.setData(self.graph_data_x, self.graph_data_y1, connect="finite")  # Update the data.
                            self.data_line2.setData(self.graph_data_x, self.graph_data_y2, connect="finite")  # Update the data.
                            self.data_line3.setData(self.graph_data_x, self.graph_data_y3, connect="finite")  # Update the data.
                    else:                        
                            self.graph_data_x.insert(self.counter, self.idx)
                            self.graph_data_y0.insert(self.counter, self.freq)
                            self.graph_data_y1.insert(self.counter, self.phasors_mag0[0])
                            self.graph_data_y2.insert(self.counter, self.phasors_mag0[1])
                            self.graph_data_y3.insert(self.counter, self.phasors_mag0[2])
                            pen0 = pg.mkPen(color=(255, 0, 0))
                            pen1 = pg.mkPen(color=(0, 255, 0))
                            pen2 = pg.mkPen(color=(0, 0, 255))
                            if self.data_line0 == 0:
                                self.data_line0 = self.graph_freq.plot(self.graph_data_x, self.graph_data_y0, connect="finite", pen=pen0)
                            else:
                                self.data_line0.setData(self.graph_data_x, self.graph_data_y0, connect='finite')  # Update the data.

                            if self.data_line1 == 0:
                                self.data_line1 = self.graph_phase.plot(self.graph_data_x, self.graph_data_y1, connect="finite", pen=pen0)
                            else:
                                self.data_line1.setData(self.graph_data_x, self.graph_data_y1, connect='finite')  # Update the data.

                            if self.data_line2 == 0:
                                self.data_line2 = self.graph_phase.plot(self.graph_data_x, self.graph_data_y2, connect="finite", pen=pen1)
                            else:
                                self.data_line2.setData(self.graph_data_x, self.graph_data_y2, connect='finite')  # Update the data.

                            if self.data_line3 == 0:
                                self.data_line3 = self.graph_phase.plot(self.graph_data_x, self.graph_data_y3, connect="finite", pen=pen2)
                            else:
                                self.data_line3.setData(self.graph_data_x, self.graph_data_y3, connect='finite')  # Update the data.
                    self.counter += 1
                    self.idx += 0.033


    def on_comboBox_clicked(self):
        index = self.comboBox.currentIndex()
        print(index)
        if index < 0:
            return

        self.label_phasors.setText(str(self.num_phasors[index]))
        self.label_analogs.setText(str(self.num_analogs[index]))
        self.label_digitals.setText(str(self.num_digitals[index]))

    def on_pushButton_connect_clicked(self):
        self.pressed += 1
        if self.pressed == 1:
            if self.pushButton_connect.text() == 'Connect':
                #print("button_clicked connected")
                if self.connected == 0:
                    self.pushButton_connect.setText('Disconnect')
                    host = str(self.host_ip.text())
                    port = int(self.host_port.text())
                    addr = (host, port)
                    self.tcpCliSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.tcpCliSock.settimeout(5)
                    # Timeout checking:
                    try:
                        self.tcpCliSock.connect((host,port))
                    except socket.timeout:
                        self.statusBar().showMessage('Socket timeout!',5000)
                        self.pushButton_connect.setText('Connect')
                        print('Socket timeout')
                        self.connected = 0
                        return

                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
                    self.tcpCliSock.send(buffer)
                    buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05'
                    self.tcpCliSock.send(buffer)
                    read_buffer = self.tcpCliSock.recv(804)
                    if read_buffer[1] == 49:
                        #print(read_buffer)
                        self.num_pmu = (read_buffer[18] << 8) + read_buffer[19]
                        nom_freq = read_buffer[107]
                        if nom_freq == 0:
                            self.nominal_freq = 60
                        else:
                            self.nominal_freq = 50
                        self.graph_freq.setYRange(self.nominal_freq-2.0, self.nominal_freq+2.0, padding=0)
                        self.label_nfreq.setText(str(self.nominal_freq))

                        self.station_name = []
                        self.num_phasors = []
                        self.num_analogs = []
                        self.num_digitals = []
                        offset = 0
                        self.offsets = []
                        self.offsets.append(16)
                        for i in range(0, self.num_pmu):
                            self.station_name.append(str(read_buffer[(20+offset):(36+offset)], 'UTF-8'))
                            self.num_phasors.append((read_buffer[40+offset] << 8) + read_buffer[41+offset])
                            self.num_analogs.append((read_buffer[42+offset] << 8) + read_buffer[43+offset])
                            self.num_digitals.append((read_buffer[44+offset] << 8) + read_buffer[45+offset])
                            offset = offset + 30 + self.num_phasors[i]*16 + self.num_phasors[i]*4
                            self.offsets.append(10+self.num_phasors[i]*8+self.offsets[i])
                            #print(self.offsets[i])
                            self.comboBox.addItem(self.station_name[i])

                        for j in range(0, self.num_pmu):
                            for i in range(0, self.num_phasors[j]):
                                if j == 0:
                                    self.phasors_mag0.append(0.0)
                                    self.phasors_phase0.append(0.0)
                                    self.phasor_name0.append(str(read_buffer[(46+16*i):(62+16*i)], 'UTF-8'))
                                    #print(self.phasor_name0[i])
                                elif j == 1:
                                    self.phasors_mag1.append(0.0)
                                    self.phasors_phase1.append(0.0)
                                    self.phasor_name1.append(str(read_buffer[(88+self.num_phasors[j-1]*16+16*i):(104+self.num_phasors[j-1]*16+16*i)], 'UTF-8'))
                                    #print(self.phasor_name1[i])
                                elif j == 2:
                                    self.phasors_mag2.append(0.0)
                                    self.phasors_phase2.append(0.0)
                                    self.phasor_name2.append(str(read_buffer[(206+self.num_phasors[j-1]*16+16*i):(222+self.num_phasors[j-1]*16+16*i)], 'UTF-8'))
                                    #print(self.phasor_name2[i])
                                elif j == 3:
                                    self.phasors_mag3.append(0.0)
                                    self.phasors_phase3.append(0.0)
                                    self.phasor_name3.append(str(read_buffer[(436+self.num_phasors[j-1]*16+16*i):(452+self.num_phasors[j-1]*16+16*i)], 'UTF-8'))
                                    #print(self.phasor_name3[i])
                        
                        print('Num Phasors list: ' + repr(self.num_phasors))
                        print('Num Analogs list: ' + repr(self.num_analogs))
                        print('Num Digitals list: ' + repr(self.num_digitals))
                        print('Offsets: '+ repr(self.offsets))
                        self.comboBox.setCurrentIndex(0)
                        self.label_phasors.setText(str(self.num_phasors[0]))
                        self.label_analogs.setText(str(self.num_analogs[0]))
                        self.label_digitals.setText(str(self.num_analogs[0]))
                        
                        for i in range(0, self.num_phasors[0]):
                            self.comboBox_2.addItem(self.phasor_name0[i])
                        self.comboBox_2.setCurrentIndex(0)


                        self.connected = 1
                        self.graph_freq.setXRange(0.0, 10.0, padding=0)
                        buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02'
                        self.tcpCliSock.send(buffer)
                        self.timer1.start(10)
                    else:
                        self.connected = 0
                        self.tcpCliSock.close()

            else:
                #print("button_clicked disconnected")
                self.connected = 0
                buffer = b'\xAA\x41\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
                self.tcpCliSock.send(buffer)
                self.timer1.stop()
                self.tcpCliSock.close()
                self.counter = 0
                self.idx = 0.0
                self.overflow = False
                self.graph_data_x.clear()
                self.graph_data_y0.clear()
                self.graph_data_y1.clear()
                self.graph_data_y2.clear()
                self.graph_data_y3.clear()
                self.graph_freq.clear()
                self.graph_phase.clear()
                self.comboBox.clear()
                self.data_line0 = 0
                self.data_line1 = 0
                self.data_line2 = 0
                self.data_line3 = 0
                self.pushButton_connect.setText('Connect')
        else:
            #print(self.pressed)
            if self.pressed == 3:
                self.pressed = 0 

            


app=QApplication(sys.argv)
widget=MainWindow()
widget.show()
sys.exit(app.exec_())
