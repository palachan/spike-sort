# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 09:41:42 2017

spike-sort with vispy

@author: Patrick
"""


import os
os.environ['QT_API'] = 'pyside'
import matplotlib as mpl
mpl.rcParams['backend.qt4']='PySide'
mpl.use('Qt4Agg')
import sys
import numpy as np
from OpenEphys import readHeader
from collections import deque
import cluster_edit
import sort_3d
import sort_waves
import avg_waves
import time_plots
from scipy.stats import iqr
import copy
import shutil

from PySide.QtCore import QRect,Qt
from PySide.QtGui import (QApplication, QMainWindow, QFrame, QLabel, QKeySequence,
                          QVBoxLayout, QHBoxLayout, QGridLayout, QShortcut,
                          QMenuBar, QMenu, QPushButton, QFileDialog, QDesktopWidget)


#class for MainWindow instance
class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        ''' sets up the whole main window '''
        
        #standard init
        super(MainWindow, self).__init__(parent)
        #set the window size in pixels
#        self.resize(1100, 700)
        #set the window title
        self.setWindowTitle('spike_sort')
        
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.screen_width = QDesktopWidget().screenGeometry().width()
        
        #assign a layout to the main window
        self.mainlayout = QGridLayout()

        #make widgets
        self.setup_mpl_canvas()
        self.setup_side_canvases()
        self.setup_param_buttons()
        self.setup_random_buttons()
        self.setup_cluster_buttons()
        self.setup_fullscreen_buttons()

        #create a QMenuBar and set geometry
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, self.screen_width*.5, self.screen_height*.03))
        #set the QMenuBar as menu bar for main window
        self.setMenuBar(self.menubar)
        
        self.setup_file_menu()
        self.setup_view_menu()

        self.new_button.clicked.connect(lambda: cluster_edit.new_cluster(self))
        self.delete_button.clicked.connect(lambda: cluster_edit.delete_cluster(self))
        self.merge_button.clicked.connect(lambda: cluster_edit.merge_clusters(self))
        
        self.plot_list = ['3D Sort','Waveforms','Avg Waveforms','ISI Histogram']
        self.canv_list = [self.plot_layout,self.plot_layout_top,self.plot_layout_mid,self.plot_layout_low]
        self.canv_labels = [self.canvas_label,self.canvas_label_top,self.canvas_label_mid,self.canvas_label_low]
        self.params = ['Peaks 1','Peaks 2','Peaks 3','Peaks 4','Valleys 1','Valleys 2','Valleys 3','Valleys 4']
        self.cs=['white','red','beige','green','skyblue','pink','limegreen','magenta','blue','purple','orange','yellow','fuchsia','greenyellow','mintcream','orchid']
        self.cs += self.cs
        
        self.set_up = False

        self.showMaximized()
        
    def open_file(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Open Spike File', '','Openephys spike files (*.spikes)')
        spike_data,self.temp_data = self.load_spikefile(self.fname[0])
        
        sample_nums = spike_data['timestamps']
        self.samplerate = spike_data['header']['sampleRate']
        #get timestamps in microseconds
        self.timestamps = np.asarray(sample_nums,dtype=np.int)
        #norm so they start at 0
#        self.timestamps = self.timestamps - np.min(self.timestamps)
        
        waveforms = np.swapaxes(spike_data['spikes'],1,2)
        self.peaks = np.max(waveforms,axis=2)
        peak_iqr = iqr(self.peaks.flatten())
        max_val = np.mean(self.peaks.flatten()) + 5*peak_iqr
        self.peaks = np.clip(self.peaks,0,max_val)
        
        self.valleys = np.min(waveforms,axis=2)
        valley_iqr = abs(iqr(self.valleys.flatten()))
        min_val = np.mean(self.valleys.flatten()) - 5*valley_iqr
        self.valleys = np.clip(self.valleys,min_val,0)

        self.energy = self.peaks**2
        
        self.num_spikes = len(waveforms)
        self.wavepoints = np.swapaxes(spike_data['spikes'],0,2)
        self.waveforms = np.swapaxes(waveforms,0,1)
        self.canvas_label.setText('3D Sort')
        self.canvas_label_top.setText('Waveforms')
        self.canvas_label_mid.setText('Avg Waveforms')
        self.canvas_label_low.setText('ISI Histogram')
        
        self.checked_clusts = []
        self.tot_clusts = 0
        
        self.cluster_dict = {}
        self.clust_buttons = {}
        self.wave_dict = {}
        self.wavepoint_dict = {}
        self.avg_wave_dict = {}
        self.isi_dict = {}
        self.timestamp_dict = {}
        self.wave_sem_dict = {}
        
        for channel in range(len(self.waveforms)):
            self.wave_dict[str(channel)] = {}
            self.wavepoint_dict[str(channel)] = {}
            self.avg_wave_dict[str(channel)] = {}
            self.wave_sem_dict[str(channel)] = {}
            
        cluster_ids = spike_data['sortedId']
        self.clusts = np.zeros(self.num_spikes,dtype=np.int)
        
        unique = np.unique(cluster_ids)
        for oe_clust in unique:
            clust = self.tot_clusts
            clust_inds = [index for index,value in enumerate(cluster_ids) if value == oe_clust]
            self.clusts[clust_inds] = clust
            self.cluster_dict[str(clust)] = [index for index,value in enumerate(self.clusts) if value == clust]
            for channel in range(len(self.wave_dict)):
                self.wave_dict[str(channel)][str(clust)] = self.waveforms[channel][self.cluster_dict[str(clust)]]
                self.wavepoint_dict[str(channel)][str(clust)] = self.wavepoints[channel][:,self.cluster_dict[str(clust)]]
                
            if int(clust) != 0:
                cluster_edit.new_cluster(self,init=True)
            self.tot_clusts += 1
                                
        if self.set_up:
            self.canv_list[0].removeWidget(self.canvas3d)
            self.canv_list[1].removeWidget(self.canvaswaves)
            self.canv_list[2].removeWidget(self.canvasavg)
            self.canv_list[3].removeWidget(self.canvasisi)
                
        self.canvas3d = sort_3d.ScatterScene(self)
        self.plot_layout.addWidget(self.canvas3d)
        
        self.canvaswaves = sort_waves.WaveformScene(self)
        self.plot_layout_top.addWidget(self.canvaswaves)
        
        self.canvasavg = avg_waves.AvgWaveformScene(self)
        self.plot_layout_mid.addWidget(self.canvasavg)
        
        self.canvasisi = time_plots.ISIScene(self)
        self.plot_layout_low.addWidget(self.canvasisi)
        
        for button in self.clust_buttons:
            self.clust_buttons[button].toggled.connect(lambda: cluster_edit.change_cluster(self))
        
        if not self.set_up:
            self.setup_shortcuts()
            self.viewMenu.addAction('&Time plot', self.canvasisi.plot_time, 'Ctrl+F4')
        
        self.param1count = 0
        self.param2count = 0
        self.param3count = 0
        
        cluster_edit.shift_clusters(self)
        
        self.set_up = True
        
    def setup_shortcuts(self):
        
        self.x_shortcut = QShortcut(QKeySequence('X'), self)
        self.x_shortcut.activated.connect(lambda: self.canvas3d.get_spike_positions(self.param1count,self.param2count,(self.param3count+1)%8))
        
        self.z_shortcut = QShortcut(QKeySequence('Z'), self)
        self.z_shortcut.activated.connect(lambda: self.canvas3d.get_spike_positions(self.param1count,self.param2count,(self.param3count-1)%8))
        
        self.s_shortcut = QShortcut(QKeySequence('S'), self)
        self.s_shortcut.activated.connect(lambda: self.canvas3d.get_spike_positions(self.param1count,(self.param2count+1)%8,self.param3count))
        
        self.a_shortcut = QShortcut(QKeySequence('A'), self)
        self.a_shortcut.activated.connect(lambda: self.canvas3d.get_spike_positions(self.param1count,(self.param2count-1)%8,self.param3count))
        
        self.w_shortcut = QShortcut(QKeySequence('W'), self)
        self.w_shortcut.activated.connect(lambda: self.canvas3d.get_spike_positions((self.param1count+1)%8,self.param2count,self.param3count))
    
        self.q_shortcut = QShortcut(QKeySequence('Q'), self)
        self.q_shortcut.activated.connect(lambda: self.canvas3d.get_spike_positions((self.param1count-1)%8,self.param2count,self.param3count))
        
        
    def load_spikefile(self,filename):
        
        data = {}
        
        f = open(filename,'rb')
        
        header = readHeader(f)
        print header
        
        data['header'] = header 
        self.numChannels = int(header['num_channels'])
        numSamples = int(40) # **NOT CURRENTLY WRITTEN TO HEADER**
        
        dt = np.dtype([('eventType', np.dtype('<u1')), ('timestamps', np.dtype('<i8')), ('software_timestamp', np.dtype('<i8')),
               ('source', np.dtype('<u2')), ('numChannels', np.dtype('<u2')), ('numSamples', np.dtype('<u2')),
               ('sortedId', np.dtype('<u2')), ('electrodeId', np.dtype('<u2')), ('channel', np.dtype('<u2')), 
               ('color', np.dtype('<u1'), 3), ('pcProj', np.float32, 2), ('sampleFreq', np.dtype('<u2')), ('waveforms', np.dtype('<u2'), self.numChannels*numSamples),
               ('gain', np.float32,self.numChannels), ('thresh', np.dtype('<u2'), self.numChannels), ('recNum', np.dtype('<u2'))])
    
        #grab the data
        temp = np.fromfile(f, dt)
                
        spikes = np.zeros((len(temp), numSamples, self.numChannels))
        
        for i in range(len(temp['waveforms'])):
        
            wv = np.reshape(temp['waveforms'][i], (self.numChannels, numSamples))
    
            for ch in range(self.numChannels):
                spikes[i,:,ch] = (np.float64(wv[ch])-32768)/(temp['gain'][i,ch]/1000)
        
        data['spikes'] = spikes
        data['timestamps'] = temp['timestamps']
        data['source'] = temp['source']
        data['gain'] = temp['gain']
        data['thresh'] = temp['thresh']
        data['recordingNumber'] = temp['recNum']
        data['sortedId'] = temp['sortedId']
        
        temp_data = copy.deepcopy(temp)
        
        return data,temp_data
        
    def save_ts(self):
        
        trodefile = os.path.basename(self.fname[0])
        save_dir = os.path.dirname(self.fname[0])
        
        for key in self.timestamp_dict.keys():
            if int(key) != 0:
                if int(key) < 10:
                    cname = '0' + key
                else:
                    cname = key
                ts_file = open(save_dir + '/' + trodefile[:3]+'_SS_'+cname+'.txt', 'w')
                for ts in self.timestamp_dict[key]:
                    ts_file.write("%s\n" % ts)
                    
        print self.timestamps
                    
    def save_spikefile(self):

        file_loc = QFileDialog.getSaveFileName(self, 'Save Spike File', self.fname[0],'Openephys spike files (*.spikes)')
        
        shutil.copyfile(self.fname[0],file_loc[0])
        
        numSamples = int(40) # **NOT CURRENTLY WRITTEN TO HEADER**
        
        dt = np.dtype([('eventType', np.dtype('<u1')), ('timestamps', np.dtype('<i8')), ('software_timestamp', np.dtype('<i8')),
               ('source', np.dtype('<u2')), ('numChannels', np.dtype('<u2')), ('numSamples', np.dtype('<u2')),
               ('sortedId', np.dtype('<u2')), ('electrodeId', np.dtype('<u2')), ('channel', np.dtype('<u2')), 
               ('color', np.dtype('<u1'), 3), ('pcProj', np.float32, 2), ('sampleFreq', np.dtype('<u2')), ('waveforms', np.dtype('<u2'), self.numChannels*numSamples),
               ('gain', np.float32,self.numChannels), ('thresh', np.dtype('<u2'), self.numChannels), ('recNum', np.dtype('<u2'))])
    
        extracted = np.memmap(file_loc[0], dtype=dt, mode='r+', 
           offset=(1024))
        
        extracted['sortedId'] = self.clusts[:len(self.clusts)]
        
        extracted.flush()

    def setup_file_menu(self):
        fileMenu = QMenu('&File',self)
        self.menubar.addMenu(fileMenu)
        
        fileMenu.addAction('&Open spike file',self.open_file, 'Ctrl+O')
        fileMenu.addAction('&Save spike file', self.save_spikefile, 'Ctrl+S')
        fileMenu.addAction('&Save timestamp file', self.save_ts, 'Ctrl+T')
        
    def setup_view_menu(self):
        self.viewMenu = QMenu('&View',self)
        self.menubar.addMenu(self.viewMenu)

    def setup_random_buttons(self):
        #make QFrame
        rb = QFrame(self)
        #set gemoetry and color
        rb.setGeometry(QRect(self.screen_width*.23, self.screen_height*.83, self.screen_width*.34, self.screen_height*.07))
        rb.setObjectName("random_buttonsWidget")
        rb.setStyleSheet("#random_buttonsWidget {background-color:gray;}")
        #create and set layout
        rb_layout = QHBoxLayout()
        rb.setLayout(rb_layout)
        #make labview checkbox
        self.new_button = QPushButton('new cluster') 
        self.new_button.setShortcut(QKeySequence('Insert'))
        self.delete_button = QPushButton('delete cluster(s)')
        self.delete_button.setShortcut(QKeySequence('Delete'))
        self.merge_button = QPushButton('merge clusters')
        self.merge_button.setShortcut(QKeySequence('Ctrl+M'))
        #add to layout
        rb_layout.addWidget(self.new_button)
        rb_layout.addWidget(self.delete_button)
        rb_layout.addWidget(self.merge_button)
        
    def setup_cluster_buttons(self):
        #make QFrame
        clusters = QFrame(self)
        #make and set label
        self.clusters_label = QLabel()
        self.clusters_label.setText('clusters')
        #set gemoetry and color
        clusters.setGeometry(QRect(self.screen_width*.36, self.screen_height*.03, self.screen_width*.34, self.screen_height*.07))
        clusters.setObjectName("clustersWidget")
        clusters.setStyleSheet("#clustersWidget {background-color:gray;}")
        #create and set layout
        self.clusters_layout = QHBoxLayout()
        clusters.setLayout(self.clusters_layout)
        #add to layout
        self.clusters_layout.addWidget(self.clusters_label)        
        self.clusters_layout.setAlignment(Qt.AlignLeft)
                
    def setup_param_buttons(self):
        #make QFrame
        params = QFrame(self)
        #make and set label
        params_label = QLabel()
        params_label.setText('3D Parameters')
        #set gemoetry and color
        params.setGeometry(QRect(self.screen_width*.02, self.screen_height*.12, self.screen_width*.07, self.screen_height*.7))
        params.setObjectName("paramsWidget")
        params.setStyleSheet("#paramsWidget {background-color:gray;}")
        #create and set layout
        params_layout = QVBoxLayout()
        params_layout.setSpacing(15)
        params.setLayout(params_layout)
        #make labview checkbox
        self.param1label = QLabel()
        self.param2label = QLabel()
        self.param3label = QLabel()

        #add to layout
        params_layout.addWidget(params_label)        
        params_layout.addWidget(self.param1label)
        params_layout.addWidget(self.param2label)
        params_layout.addWidget(self.param3label)
        params_layout.setAlignment(Qt.AlignTop)
            
    def setup_fullscreen_buttons(self):
        fsb1 = QFrame(self)
        fsb1.setGeometry(QRect(self.screen_width*.9, self.screen_height*.085, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button1 = QPushButton('full')
        fsb1_layout = QHBoxLayout()
        fsb1_layout.addWidget(self.fullscreen_button1)
        fsb1.setLayout(fsb1_layout)
        
        fsb2 = QFrame(self)
        fsb2.setGeometry(QRect(self.screen_width*.9, self.screen_height*.355, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button2 = QPushButton('full')
        fsb2_layout = QHBoxLayout()
        fsb2_layout.addWidget(self.fullscreen_button2)
        fsb2.setLayout(fsb2_layout)
        
        fsb3 = QFrame(self)
        fsb3.setGeometry(QRect(self.screen_width*.9, self.screen_height*.635, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button3 = QPushButton('full')
        fsb3_layout = QHBoxLayout()
        fsb3_layout.addWidget(self.fullscreen_button3)
        fsb3.setLayout(fsb3_layout)
        
        self.fullscreen_button1.clicked.connect(lambda: self.change_plots(1))
        self.fullscreen_button2.clicked.connect(lambda: self.change_plots(2))
        self.fullscreen_button3.clicked.connect(lambda: self.change_plots(3))
        
    def setup_mpl_canvas(self):
        ''' set up the matplotlib plotting canvas '''
        
        #create QFrame with parent self
        plot_frame = QFrame(self)
        #make a label for the canvas
        self.canvas_label = QLabel()
        #make label empty for now
        self.canvas_label.setText('')
        #set geometry
        plot_frame.setGeometry(QRect(self.screen_width*.1, self.screen_height*.12, self.screen_width*.6, self.screen_height*.7))
        #name the QFrame so we can give it a cool color
        plot_frame.setObjectName("main_canvas_widget")
        #give it a cool color
        plot_frame.setStyleSheet("#main_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        self.plot_layout = QVBoxLayout()
        plot_frame.setLayout(self.plot_layout)

    
    def setup_side_canvases(self):
        ''' set up bonus plotting canvases '''
        
        #create QFrame with parent self
        plot_frame_top = QFrame(self)
        #make a label for the canvas
        self.canvas_label_top = QLabel()
        #make label empty for now
        self.canvas_label_top.setText('')
        #set geometry
        plot_frame_top.setGeometry(QRect(self.screen_width*.72, self.screen_height*.1, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_top.setObjectName("top_canvas_widget")
        #give it a cool color
        plot_frame_top.setStyleSheet("#top_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        self.plot_layout_top = QVBoxLayout()
        plot_frame_top.setLayout(self.plot_layout_top)
        #add canvas and label to layout
        self.plot_layout_top.addWidget(self.canvas_label_top)
        
        
        #create QFrame with parent self
        plot_frame_mid = QFrame(self)
        #make a label for the canvas
        self.canvas_label_mid = QLabel()
        #make label empty for now
        self.canvas_label_mid.setText('')
        #set geometry
        plot_frame_mid.setGeometry(QRect(self.screen_width*.72, self.screen_height*.37, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_mid.setObjectName("mid_canvas_widget")
        #give it a cool color
        plot_frame_mid.setStyleSheet("#mid_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        self.plot_layout_mid = QVBoxLayout()
        plot_frame_mid.setLayout(self.plot_layout_mid)
        #add canvas and label to layout
        self.plot_layout_mid.addWidget(self.canvas_label_mid)
#        plot_layout_mid.addWidget(self.midcanvas)
        
        #create QFrame with parent self
        plot_frame_low = QFrame(self)
        #make a label for the canvas
        self.canvas_label_low = QLabel()
        #make label empty for now
        self.canvas_label_low.setText('')
        #set geometry
        plot_frame_low.setGeometry(QRect(self.screen_width*.72, self.screen_height*.65, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_low.setObjectName("low_canvas_widget")
        #give it a cool color
        plot_frame_low.setStyleSheet("#low_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        self.plot_layout_low = QVBoxLayout()
        plot_frame_low.setLayout(self.plot_layout_low)
        #add canvas and label to layout
        self.plot_layout_low.addWidget(self.canvas_label_low)
#        plot_layout_low.addWidget(self.lowcanvas)
        
    def change_plots(self,button):
        
        def rotate(lst, x):
            d = deque(lst)
            d.rotate(x)
            lst[:] = d
            return lst

        self.canv_list[0].removeWidget(self.canvas3d)
        self.canv_list[1].removeWidget(self.canvaswaves)
        self.canv_list[2].removeWidget(self.canvasavg)
        self.canv_list[3].removeWidget(self.canvasisi)

        self.canv_list = rotate(self.canv_list,button)
        self.canv_labels = rotate(self.canv_labels,button)
        
        self.canv_list[0].addWidget(self.canvas3d)
        self.canv_list[1].addWidget(self.canvaswaves)
        self.canv_list[2].addWidget(self.canvasavg)
        self.canv_list[3].addWidget(self.canvasisi)
        
        self.canv_labels[0].setText(self.plot_list[0])
        self.canv_labels[1].setText(self.plot_list[1])
        self.canv_labels[2].setText(self.plot_list[2])
        self.canv_labels[3].setText(self.plot_list[3])
        

''''''''''''''''''''''''''''''''''''''''''''''''''''''
######################################################
''''''''''''''''''''''''''''''''''''''''''''''''''''''
        
if __name__ == '__main__':
    #create a QApplication if one doesn't already exist
    app = QApplication.instance()
    if app == None:
        app = QApplication(['/Users/Patrick/anaconda/lib/python2.7/site-packages/spyderlib/widgets/externalshell/start_ipython_kernel.py'])
    
    #create and show the main window
    frame = MainWindow()
    frame.show()
    
    #exit the app when we're all done
    sys.exit(app.exec_())