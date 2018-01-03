# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 09:41:42 2017

spike-sort with vispy

@author: Patrick
"""
#import necessary modules
import os
import sys
import numpy as np
from OpenEphys import readHeader
from collections import deque
from scipy.stats import iqr
from sklearn.decomposition import PCA
import copy
import shutil

#import functions from other sort scripts
import cluster_edit
import sort_3d
import sort_waves
import avg_waves
import time_plots

#import GUI objects/Widgets
from PySide.QtCore import QRect,Qt
from PySide.QtGui import (QApplication, QMainWindow, QFrame, QLabel, QKeySequence,
                          QVBoxLayout, QHBoxLayout, QGridLayout, QShortcut, QWidget, QLineEdit,
                          QMenuBar, QMenu, QPushButton, QFileDialog, QDesktopWidget, QComboBox)

#make sure we're using the right qt API
os.environ['QT_API'] = 'pyside'


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Let's begin!
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


#class for MainWindow instance
class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        ''' sets up the whole main window '''
        
        #standard init
        super(MainWindow, self).__init__(parent)

        #set the window title
        self.setWindowTitle('spike-sort')
        
        #get screen dimensions
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.screen_width = QDesktopWidget().screenGeometry().width()
        
        #assign a layout to the main window
        self.mainlayout = QGridLayout()

        #create a QMenuBar and set geometry
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, self.screen_width*.5, self.screen_height*.03))
        #set the QMenuBar as menu bar for main window
        self.setMenuBar(self.menubar)
        
        #setup menus within the menu bar (File,View,Params)
        self.setup_file_menu()
        self.setup_view_menu()
        self.setup_param_menu()
        
        #make widgets
        self.setup_vispy_canvas()
        self.setup_side_canvases()
        self.setup_param_buttons()
        self.setup_random_buttons()
        self.setup_cluster_buttons()
        self.setup_fullscreen_buttons()
        self.setup_kmeans()

        #connect cluster_edit buttons to their respective functions in the cluster_edit script
        self.new_button.clicked.connect(lambda: cluster_edit.new_cluster(self))
        self.delete_button.clicked.connect(lambda: cluster_edit.delete_cluster(self))
        self.merge_button.clicked.connect(lambda: cluster_edit.merge_clusters(self))
        
        #list of plots in the main window
        self.plot_list = ['3D Sort','Waveforms','Avg Waveforms','ISI Histogram']
        #list of canvases (locations for each plot - matches plot list)
        self.canv_list = [self.plot_layout,self.plot_layout_top,self.plot_layout_mid,self.plot_layout_low]
        #labels for each canvas
        self.canv_labels = [self.canvas_label,self.canvas_label_top,self.canvas_label_mid,self.canvas_label_low]
        #start parameters for 3D sort
        self.params = ['Peaks 1','Peaks 2','Peaks 3','Peaks 4','Valleys 1','Valleys 2','Valleys 3','Valleys 4']
        #parameters we can choose from later
        self.paramchoices = ['Peaks','Valleys','Energy','PC1','PC2','PC3','Real PC1']
        #cluster colors
        self.cs=['white','red','beige','green','skyblue','pink','limegreen','magenta','blue','purple','orange','yellow','fuchsia','greenyellow','mintcream','orchid']
        #double the color list so we can have even more clusters !
        self.cs += self.cs
        
        #note that we haven't initialized anything important yet
        self.set_up = False

        #show the window fullscreen
        self.showMaximized()
        
    def open_file(self):
        ''' loads an openephys .spikes file for clustering '''
        
        #grab the file we want to open
        self.fname = QFileDialog.getOpenFileName(self, 'Open Spike File', '','Openephys spike files (*.spikes)')
        #load relevant data from the spike file
        spike_data = self.load_spikefile(self.fname[0])
        
        #grab timestamps from the data (actually sample numbers)
        self.timestamps = np.asarray(spike_data['timestamps'],np.int)
        #grab the sampling rate from the file header (probably 30 kHz)
        self.samplerate = spike_data['header']['sampleRate']
        
        #grab waveforms from the data, flip
        waveforms = spike_data['spikes'] * -1
        #grab important info from the waveforms array
        self.num_spikes,self.num_samples,self.num_channels = np.shape(waveforms)
        
        #calculate peaks for each waveform
        self.peaks = np.swapaxes(np.max(waveforms,axis=1),0,1)
        #find the IQR of the peaks to limit the data
        peak_iqr = iqr(self.peaks.flatten())
        #assign a maximum peak value
        max_val = np.mean(self.peaks.flatten()) + 5*peak_iqr
        #clip the peaks to that value
        self.peaks = np.clip(self.peaks,0,max_val)
        
        #calculate valleys for each waveform
        self.valleys = np.swapaxes(np.min(waveforms,axis=1),0,1)
        #find IQR
        valley_iqr = abs(iqr(self.valleys.flatten()))
        #assign a minimum valley value
        min_val = np.mean(self.valleys.flatten()) - 5*valley_iqr
        #clip the valleys to that value
        self.valleys = np.clip(self.valleys,min_val,0)
        
        #calculate energy (E = sqrt(SS(wave))/num_samples)
        self.energy = np.swapaxes(np.sqrt(np.sum(waveforms**2,axis=1))/self.num_samples,0,1)
        #scale the energy values to be similar to peak values for visualization purposes
        mean_peak = np.mean(self.peaks)
        mean_energy = np.mean(self.energy)
        self.energy *= mean_peak/mean_energy
        #find the IQR of the energy to limit the data
        energy_iqr = iqr(self.energy.flatten())
        #assign a maximum energy value
        max_val = np.mean(self.energy.flatten()) + 5*energy_iqr
        #clip the peaks to that value
        self.energy = np.clip(self.energy,0,max_val)
        
        #swap axes for waveforms (so shape (numchannels,numspikes,numsamples)) #TODO: necessary?
        self.waveforms = np.swapaxes(np.swapaxes(waveforms,1,2),0,1)
        #calculate principal components
        self.calc_principal_components()
        
        #set text for canvas labels
        self.canvas_label.setText('3D Sort')
        self.canvas_label_top.setText('Waveforms')
        self.canvas_label_mid.setText('Avg Waveforms')
        self.canvas_label_low.setText('ISI Histogram')
        
        #if we're opening up a NEW spike file...
        if self.set_up:
            #remove all the active cluster labels from the params layout
            for label in self.clust_labels:
                if self.clust_labels[label] is not None:
                    self.clust_labels[label].setText('')
                    self.params_layout.removeWidget(self.clust_labels[label])
            #remove old plots from canvases
            self.canv_list[0].removeWidget(self.canvas3d)
            self.canv_list[1].removeWidget(self.canvaswaves)
            self.canv_list[2].removeWidget(self.canvasavg)
            self.canv_list[3].removeWidget(self.canvasisi)
        
        ''' initialize a ton of dictionaries and lists '''
        #list to hold active clusters
        self.checked_clusts = []
        #counter to hold number of clusters
        self.tot_clusts = 0
        #array to hold cluster identities for each spike
        self.clusts = np.zeros(self.num_spikes,dtype=np.int)
        #dict to hold spike indices for each cluster
        self.cluster_dict = {}
        #dict to hold button widgets for clusters
        self.clust_buttons = {}
        #dict to hold label widgets for each cluster
        self.clust_labels = {}
        #dict to hold waveforms for each cluster
        self.wave_dict = {}
        #dict to hold average waveforms for each cluster
        self.avg_wave_dict = {}
        #dict to hold SEMs for average waveforms
        self.wave_sem_dict = {}
        #dict to hold ISIs for each cluster
        self.isi_dict = {}
        #dict to hold timestamps for each cluster
        self.timestamp_dict = {}
        #dict to hold lratios for each cluster
        self.lratios = {}
        #dict to hold isolation distances for each cluster
        self.iso_dists = {}
        
        #initialize entries for each channel in waveform dicts
        for channel in range(self.num_channels):
            self.wave_dict[str(channel)] = {}
            self.avg_wave_dict[str(channel)] = {}
            self.wave_sem_dict[str(channel)] = {}
            
        #grab assigned cluster numbers from spike file
        cluster_ids = spike_data['sortedId']
        
        #find the unique cluster numbers
        unique = np.unique(cluster_ids)
        #for each unique cluster...
        for oe_clust in unique:
            #get the current cluster number (based on current number of 
            #unique clusters)
            clust = self.tot_clusts
            #get spike indices for that cluster from cluster_ids  list
            clust_inds = [index for index,value in enumerate(cluster_ids) if value == oe_clust]
            #assign spike number to appropriate indices in clusts list
            self.clusts[clust_inds] = clust
            #assign indices to appropriate entry in cluster_dict
            self.cluster_dict[str(clust)] = clust_inds
            #for each channel...
            for channel in range(self.num_channels):
                #add waveforms to appropriate entry in wveform dicts
                self.wave_dict[str(channel)][str(clust)] = self.waveforms[channel][self.cluster_dict[str(clust)]]
                
            #if the current cluster ID isn't zero...
            if int(clust) != 0:
                #add a new cluster button
                cluster_edit.new_cluster(self,init=True)
                
            self.tot_clusts += 1

        #initialize 3D clustering plot                
        self.canvas3d = sort_3d.ScatterScene(self)
        #add to appropriate canvas
        self.plot_layout.addWidget(self.canvas3d)
        
        #initialize waveform plot
        self.canvaswaves = sort_waves.WaveformScene(self)
        #add to appropriate canvas
        self.plot_layout_top.addWidget(self.canvaswaves)
        
        #initialize avg waveform plot
        self.canvasavg = avg_waves.AvgWaveformScene(self)
        #add to appropriate canvas
        self.plot_layout_mid.addWidget(self.canvasavg)
        
        #initialize ISI histogram plot
        self.canvasisi = time_plots.ISIScene(self)
        #add to appropriate canvas
        self.plot_layout_low.addWidget(self.canvasisi)
        
        #for each cluster button...
        for button in self.clust_buttons:
            #connect to cluster_edit 'change cluster' function
            self.clust_buttons[button].toggled.connect(lambda: cluster_edit.change_cluster(self))

        #to keep track of which variables in params list we're currently using
        #to sort
        self.param1count = 0
        self.param2count = 1
        self.param3count = 2
        
        #get spike positions for 3D sorting according to current params
        self.canvas3d.get_spike_positions(self.param1count,self.param2count,self.param3count)
        
        #if this is the first time we're setting stuff up...
        if not self.set_up:
            #add a spacer between param labels and cluster info
            spacer = QLabel('---------------------------')
            self.params_layout.addWidget(spacer)
            #set up keyboard shortcuts
            self.setup_shortcuts()
            #set up time plot in view menu
            self.viewMenu.addAction('&Time plot', self.canvasisi.plot_time, 'Ctrl+F4')
            #connect the kmeans button to the kmeans function
            self.kmeans_button.clicked.connect(lambda: cluster_edit.kmeans(self,int(self.kmeans_box.text())))
        
        #pass off to cluster_edit to take care of the rest
        cluster_edit.shift_clusters(self)
        
        #note that we've now definitely set stuff up
        self.set_up = True
        
    def calc_principal_components(self):
        ''' calculate the first 3 principal components of the waveforms '''
        
        #set up arrays for principal components
        self.pc1 = np.zeros_like(self.peaks)
        self.pc2 = np.zeros_like(self.peaks)
        self.pc3 = np.zeros_like(self.peaks)
        #will talk about this one later
        self.realpc1 = np.zeros_like(self.peaks)
                
        #set up array for energies to normalize waveforms by (from Redish 2005,
        #this causes principal components to be based on waveform shape rather than
        #amplitude or other size factors)
        #we need to broadcast the energies to fill an array the size of waveforms array
        broadcasted_energies = np.zeros_like(self.waveforms[0,:])
                
        #for each channel...
        for channel in range(self.num_channels):
            #copy energy array for that channel
            energies = copy.deepcopy(self.energy[channel])
            #for each spike...
            for i in range(self.num_spikes):
                #for each sample...
                for j in range(self.num_samples):
                    #assign the appropriate energy to the array
                    broadcasted_energies[i][j] = energies[i]
                    #if no energy, set to 1 (to avoid division error)
                    if energies[i] == 0:
                        broadcasted_energies[i][j] = 1  
                        
            #set up a PCA function to return first 3 components
            pca=PCA(n_components=3)
            #transform the waveforms (normalized by energy) into PC space
            new_vals = pca.fit_transform(self.waveforms[channel,:]/broadcasted_energies)
            #grab the first three principal components
            self.pc1[channel] = new_vals[:,0]
            self.pc2[channel] = new_vals[:,1]
            self.pc3[channel] = new_vals[:,2]
            
            #also compute first PC not normalized by energy, for visualization purposes
            pca = PCA(n_components=1)
            new_vals = pca.fit_transform(self.waveforms[channel,:])
            self.realpc1[channel]=new_vals[:,0]
            
        ''' set limits for every principal component '''
        #find the IQR of the pc to limit the data
        pc_iqr = iqr(self.pc1.flatten())
        #assign a maximum pc value
        max_val = np.mean(self.pc1.flatten()) + 5*pc_iqr
        #assign a minimum pc value
        min_val = np.mean(self.pc1.flatten()) - 5*pc_iqr
        #clip the pcs to that value
        self.pc1 = np.clip(self.pc1,min_val,max_val)
        
        #find the IQR of the pc to limit the data
        pc_iqr = iqr(self.pc2.flatten())
        #assign a maximum pc value
        max_val = np.mean(self.pc2.flatten()) + 5*pc_iqr
        #assign a minimum pc value
        min_val = np.mean(self.pc2.flatten()) - 5*pc_iqr
        #clip the pcs to that value
        self.pc2 = np.clip(self.pc2,min_val,max_val)
        
        #find the IQR of the pc to limit the data
        pc_iqr = iqr(self.pc3.flatten())
        #assign a maximum pc value
        max_val = np.mean(self.pc3.flatten()) + 5*pc_iqr
        #assign a minimum pc value
        min_val = np.mean(self.pc3.flatten()) - 5*pc_iqr
        #clip the pcs to that value
        self.pc3 = np.clip(self.pc3,min_val,max_val)
        
        #find the IQR of the pc to limit the data
        pc_iqr = iqr(self.realpc1.flatten())
        #assign a maximum pc value
        max_val = np.mean(self.realpc1.flatten()) + 5*pc_iqr
        #assign a minimum pc value
        min_val = np.mean(self.realpc1.flatten()) - 5*pc_iqr
        #clip the pcs to that value
        self.realpc1 = np.clip(self.realpc1,min_val,max_val)
        
        ''''''

        #set up array for lratio computing values (energy and first PC)
        self.all_points = np.zeros((8,self.num_spikes))
        
        #assign feature values to array
        self.all_points[0] = self.energy[0]
        self.all_points[1] = self.energy[1]
        self.all_points[2] = self.energy[2]
        self.all_points[3] = self.energy[3]
        self.all_points[4] = self.pc1[0]
        self.all_points[5] = self.pc1[1]
        self.all_points[6] = self.pc1[2]
        self.all_points[7] = self.pc1[3]

    def change_params(self):
        ''' popup window to change parameters used in 3D sort '''
        
        #create window as parentless QWidget, resize
        self.param_window = QWidget()
        self.param_window.resize(400, 350)
        #set title
        self.param_window.setWindowTitle('Select Parameters')
        #give grid layout, set fixed spacing
        windowlayout = QGridLayout(self.param_window)
        windowlayout.setSpacing(15)
        
        #make list of available electrodes based on probe type
        if self.num_channels == 4:
            trodenums = ['1','2','3','4']
        elif self.num_channels == 2:
            trodenums = ['1','2']
        
        #make dicts to hold electrode and parameter selection widgets
        electrodes = {}
        paramboxes = {}
        
        #create labels for each column of choices
        paramlabel = QLabel('Parameter')
        trodelabel = QLabel('Electrode')
        #add the labels to the grid layout
        windowlayout.addWidget(paramlabel,0,1,1,1)
        windowlayout.addWidget(trodelabel,0,2,1,1)
        
        #for each parameter choice...
        for i in range(1,9):
            #create a label, add to layout
            label = QLabel('Param %d' % i)
            label.setAlignment(Qt.AlignCenter)
            windowlayout.addWidget(label,i,0,1,1)
            
            #create a drop-down menu for electrode numbers
            electrodes[str(i)] = QComboBox(self.param_window)
            electrodes[str(i)].addItems(trodenums) 
            #show current selection
            current_channel = (self.params[i-1][len(self.params[i-1])-1])
            current_ind = trodenums.index(current_channel)
            electrodes[str(i)].setCurrentIndex(current_ind)
            #add menu to layout
            windowlayout.addWidget(electrodes[str(i)],i,2,1,1)
            
            #create a drop-down menu for parameter options
            paramboxes[str(i)] = QComboBox(self.param_window)
            paramboxes[str(i)].addItems(self.paramchoices)
            #show current selection
            current_param = self.params[i-1][:len(self.params[i-1])-2]
            current_ind = self.paramchoices.index(current_param)
            paramboxes[str(i)].setCurrentIndex(current_ind)
            #add menu to layout
            windowlayout.addWidget(paramboxes[str(i)],i,1,1,1)
            
        def select_params_and_exit(self,paramboxes,electrodes):
            ''' function just to apply changes and close popup '''
            
            #for each parameter choice...
            for i in range(1,9):
                #set appropriate parameter in params list
                self.params[i-1] = paramboxes[str(i)].currentText() + ' ' + electrodes[str(i)].currentText()
                
            #if we're all set up...
            if self.set_up:
                #tell the 3D sort plot to update 
                self.canvas3d.get_spike_positions(self.param1count,self.param2count,self.param3count)
                
            #close the window
            self.param_window.close()
            
        #add a button to apply changes/close
        ok_button = QPushButton('OK')
        #connect to appropriate function, add to layout
        ok_button.clicked.connect(lambda: select_params_and_exit(self,paramboxes,electrodes))
        windowlayout.addWidget(ok_button,10,1,1,1)
        
        #show the window
        self.param_window.show()

    def setup_shortcuts(self):
        ''' set up shortcut keys for parameter changes '''
        
        #pretty self-explanatory
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
        ''' loads an openephys .spikes file '''
        
        #make a dict to hold relevant data
        data = {}
        #open the file we're reading from
        f = open(filename,'rb')
        #read the header
        header = readHeader(f)
        #assign header to data dict
        data['header'] = header
        #grab number of channels and samples per spike from the header
        numChannels = int(header['num_channels'])
        numSamples = int(40) # **NOT CURRENTLY WRITTEN TO HEADER**
                
        #define the data types for reading the file
        dt = np.dtype([('eventType', np.dtype('<u1')), ('timestamps', np.dtype('<i8')), ('software_timestamp', np.dtype('<i8')),
               ('source', np.dtype('<u2')), ('numChannels', np.dtype('<u2')), ('numSamples', np.dtype('<u2')),
               ('sortedId', np.dtype('<u2')), ('electrodeId', np.dtype('<u2')), ('channel', np.dtype('<u2')), 
               ('color', np.dtype('<u1'), 3), ('pcProj', np.float32, 2), ('sampleFreq', np.dtype('<u2')), ('waveforms', np.dtype('<u2'), numChannels*numSamples),
               ('gain', np.float32,numChannels), ('thresh', np.dtype('<u2'), numChannels), ('recNum', np.dtype('<u2'))])
        
        #grab the data
        temp = np.fromfile(f, dt)
                
        #create an array for holding waveforms
        spikes = np.zeros((len(temp), numSamples, numChannels))
        #for each spike in waveforms array...
        for i in range(len(temp['waveforms'])):
            #reshape to be in shape (numChannels,numSamples)
            wv = np.reshape(temp['waveforms'][i], (numChannels, numSamples))
            #for each channel...
            for ch in range(numChannels):
                #convert values to volts and assign to spikes dict
                spikes[i,:,ch] = (np.float64(wv[ch])-32768)/(temp['gain'][i,ch]/1000)
        
        #assign relevant data to data dict
        data['spikes'] = spikes
        data['timestamps'] = temp['timestamps']
        data['source'] = temp['source']
        data['gain'] = temp['gain']
        data['thresh'] = temp['thresh']
        data['recordingNumber'] = temp['recNum']
        data['sortedId'] = temp['sortedId']
        
        #return our data
        return data
        
    def save_ts(self):
        ''' save timestamp .txt file for each cluster '''
        
        #grab the name of the spike file and its directory
        trodefile = os.path.basename(self.fname[0])
        save_dir = os.path.dirname(self.fname[0])
        
        #for each available cluster...
        for key in self.timestamp_dict.keys():
            #if it's not cluster zero...
            if int(key) != 0:
                #name the file according to cluster number 
                if int(key) < 10:
                    cname = '0' + key
                else:
                    cname = key
                #open the file 
                ts_file = open(save_dir + '/' + trodefile[:3]+'_SS_'+cname+'.txt', 'w')
                #write the timestamps
                for ts in self.timestamp_dict[key]:
                    ts_file.write("%s\n" % ts)
                                        
    def save_spikefile(self):
        ''' saves a new copy of (or overwrites) the original .spikes file including cluster data '''

        #ask for a save location
        file_loc = QFileDialog.getSaveFileName(self, 'Save Spike File', self.fname[0],'Openephys spike files (*.spikes)')
        
        #if it's not the original file location/name, copy the original file to
        #the new directory
        if self.fname[0] != file_loc[0]:
            shutil.copyfile(self.fname[0],file_loc[0])
        
        numSamples = int(40) # **NOT CURRENTLY WRITTEN TO HEADER**
        
        #define data types for writing
        dt = np.dtype([('eventType', np.dtype('<u1')), ('timestamps', np.dtype('<i8')), ('software_timestamp', np.dtype('<i8')),
               ('source', np.dtype('<u2')), ('numChannels', np.dtype('<u2')), ('numSamples', np.dtype('<u2')),
               ('sortedId', np.dtype('<u2')), ('electrodeId', np.dtype('<u2')), ('channel', np.dtype('<u2')), 
               ('color', np.dtype('<u1'), 3), ('pcProj', np.float32, 2), ('sampleFreq', np.dtype('<u2')), ('waveforms', np.dtype('<u2'), self.num_channels*numSamples),
               ('gain', np.float32,self.num_channels), ('thresh', np.dtype('<u2'), self.num_channels), ('recNum', np.dtype('<u2'))])
        
        #memory map the file, skipping the header
        extracted = np.memmap(file_loc[0], dtype=dt, mode='r+', 
           offset=(1024))
        
        #change the 'sortedId' data to match current clusters
        extracted['sortedId'] = self.clusts[:len(self.clusts)]
        
        #flush changes to disk and close the file
        extracted.flush()
        extracted.close()

    def setup_file_menu(self):
        ''' sets up a File dropdown menu '''
        
        #create QMenu, add to menubar
        fileMenu = QMenu('&File',self)
        self.menubar.addMenu(fileMenu)
        
        #add open and save functions/entries to the menu
        fileMenu.addAction('&Open spike file',self.open_file, 'Ctrl+O')
        fileMenu.addAction('&Save spike file', self.save_spikefile, 'Ctrl+S')
        fileMenu.addAction('&Save timestamp file', self.save_ts, 'Ctrl+T')
        
    def setup_view_menu(self):
        ''' sets up a View dropdown menu '''
        
        #create QMenu, add to menubar
        self.viewMenu = QMenu('&View',self)
        self.menubar.addMenu(self.viewMenu)
        
    def setup_param_menu(self):
        ''' sets up a Params dropdown menu '''
        
        #create QMenu, add to menubar
        paramMenu = QMenu('&Params',self)
        self.menubar.addMenu(paramMenu)
        
        #add parameter selection function/entry
        paramMenu.addAction('&Select Parameters', self.change_params, 'Ctrl+P')

    def setup_random_buttons(self):
        ''' sets up cluster-related buttons/frame '''
        
        #make QFrame
        rb = QFrame(self)
        #set gemoetry and color
        rb.setGeometry(QRect(self.screen_width*.23, self.screen_height*.83, self.screen_width*.34, self.screen_height*.07))
        rb.setObjectName("random_buttonsWidget")
        rb.setStyleSheet("#random_buttonsWidget {background-color:gray;}")
        #create and set layout
        rb_layout = QHBoxLayout()
        rb.setLayout(rb_layout)
        #make buttons for new cluster, delete, and merge - also add shortcuts
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
        ''' sets up frame for holding buttons used to select clusters '''
        
        #make QFrame
        clusters = QFrame(self)
        #make and set label
        self.clusters_label = QLabel()
        self.clusters_label.setText('clusters')
        #set gemoetry and color
        clusters.setGeometry(QRect(self.screen_width*.1, self.screen_height*.03, self.screen_width*.5, self.screen_height*.07))
        clusters.setObjectName("clustersWidget")
        clusters.setStyleSheet("#clustersWidget {background-color:gray;}")
        #create and set layout
        self.clusters_layout = QHBoxLayout()
        clusters.setLayout(self.clusters_layout)
        #add to layout
        self.clusters_layout.addWidget(self.clusters_label)        
        self.clusters_layout.setAlignment(Qt.AlignLeft)
        
    def setup_kmeans(self):
        ''' sets up interface for performing kmeans clustering '''
        
        #make QFrame
        kmeans = QFrame(self)
        #make and set label
        kmeans_label = QLabel()
        kmeans_label.setText('# clusters')
        #set gemoetry and color
        kmeans.setGeometry(QRect(self.screen_width*.61, self.screen_height*.03, self.screen_width*.09, self.screen_height*.07))
        kmeans.setObjectName("kmeansWidget")
        kmeans.setStyleSheet("#kmeansWidget {background-color:gray;}")
        #create and set layout
        kmeans_layout = QHBoxLayout()
        kmeans.setLayout(kmeans_layout)
   
        #make user interface for kmeans
        self.kmeans_box = QLineEdit()
        self.kmeans_button = QPushButton('KMeans')
    
        #add widgets to layout
        kmeans_layout.addWidget(kmeans_label)
        kmeans_layout.addWidget(self.kmeans_box)
        kmeans_layout.addWidget(self.kmeans_button)
        #set alignment
        kmeans_layout.setAlignment(Qt.AlignLeft)
                
    def setup_param_buttons(self):
        ''' sets up labels for showing which 3D parameters are active '''
        
        #make QFrame
        params = QFrame(self)
        #make and set label
        params_label = QLabel()
        params_label.setText('3D Parameters')
        #set gemoetry and color
        params.setGeometry(QRect(self.screen_width*.02, self.screen_height*.12, self.screen_width*.07, self.screen_height*.7))
        params.setObjectName("paramsWidget")
        params.setStyleSheet("#paramsWidget {background-color:gray;}")
        #create and set layout, fixed spacing
        self.params_layout = QVBoxLayout()
        self.params_layout.setSpacing(15)
        params.setLayout(self.params_layout)
        #make parameter labels
        self.param1label = QLabel()
        self.param2label = QLabel()
        self.param3label = QLabel()

        #add to layout
        self.params_layout.addWidget(params_label)        
        self.params_layout.addWidget(self.param1label)
        self.params_layout.addWidget(self.param2label)
        self.params_layout.addWidget(self.param3label)
        #set alignment
        self.params_layout.setAlignment(Qt.AlignTop)
            
    def setup_fullscreen_buttons(self):
        ''' sets up buttons for moving smaller plots to the main canvas '''
        
        #create a QFrame for top canvas, set location/geometry
        fsb1 = QFrame(self)
        fsb1.setGeometry(QRect(self.screen_width*.9, self.screen_height*.085, self.screen_width*.055, self.screen_height*.06))
        #create a "Full" button to put on the frame
        self.fullscreen_button1 = QPushButton('full')
        #create a layout, add the button
        fsb1_layout = QHBoxLayout()
        fsb1_layout.addWidget(self.fullscreen_button1)
        fsb1.setLayout(fsb1_layout)
        
        #repeat for middle canvas
        fsb2 = QFrame(self)
        fsb2.setGeometry(QRect(self.screen_width*.9, self.screen_height*.355, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button2 = QPushButton('full')
        fsb2_layout = QHBoxLayout()
        fsb2_layout.addWidget(self.fullscreen_button2)
        fsb2.setLayout(fsb2_layout)
        
        #repeat for bottom canvas
        fsb3 = QFrame(self)
        fsb3.setGeometry(QRect(self.screen_width*.9, self.screen_height*.635, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button3 = QPushButton('full')
        fsb3_layout = QHBoxLayout()
        fsb3_layout.addWidget(self.fullscreen_button3)
        fsb3.setLayout(fsb3_layout)
        
        #connect buttons to change_plots function with argument specifying
        #which button was pushed
        self.fullscreen_button1.clicked.connect(lambda: self.change_plots(1))
        self.fullscreen_button2.clicked.connect(lambda: self.change_plots(2))
        self.fullscreen_button3.clicked.connect(lambda: self.change_plots(3))
        
    def setup_vispy_canvas(self):
        ''' set up the main vispy plotting canvas '''
        
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
        
    def change_plots(self,button):
        ''' moves plots around according to which 'Full' button was pressed '''
        
        def rotate(lst, x):
            ''' little function to rotate list '''
            d = deque(lst)
            d.rotate(x)
            lst[:] = d
            return lst

        #remove all the plots from their respective canvases
        self.canv_list[0].removeWidget(self.canvas3d)
        self.canv_list[1].removeWidget(self.canvaswaves)
        self.canv_list[2].removeWidget(self.canvasavg)
        self.canv_list[3].removeWidget(self.canvasisi)

        #rotate the canvas and labels lists
        self.canv_list = rotate(self.canv_list,button)
        self.canv_labels = rotate(self.canv_labels,button)
        
        #add the plots to their new canvases
        self.canv_list[0].addWidget(self.canvas3d)
        self.canv_list[1].addWidget(self.canvaswaves)
        self.canv_list[2].addWidget(self.canvasavg)
        self.canv_list[3].addWidget(self.canvasisi)
        
        #assign appropriate label text to each canvas label
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