# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 11:09:38 2017

handles cluster stuff, like adding, deleting, merging, etc.

@author: Patrick
"""

import copy
import numpy as np
from PySide.QtGui import QPushButton,QKeySequence

def new_cluster(self,init=False):
    
    if not init:
        self.tot_clusts += 1
        
    this_clust = int(copy.deepcopy(self.tot_clusts))

    self.clust_buttons[str(this_clust)] = QPushButton(str(this_clust))
    self.clust_buttons[str(this_clust)].setCheckable(True)
    self.clust_buttons[str(this_clust)].setStyleSheet('QPushButton {background-color: %s}' % self.cs[this_clust])
    self.clusters_layout.addWidget(self.clust_buttons[str(this_clust)])
    
    if not init:
        self.cluster_dict[str(this_clust)] = []
        
        for channel in range(len(self.waveforms)):
            self.wave_dict[str(channel)][str(this_clust)] = []
            self.wavepoint_dict[str(channel)][str(this_clust)] = []
    
    for key in self.clust_buttons:
        self.clust_buttons[key].setChecked(False)
    self.clust_buttons[str(this_clust)].setChecked(True)
    if not init:
        self.clust_buttons[str(this_clust)].toggled.connect(lambda: change_cluster(self))
    
    self.clust_buttons[str(this_clust)].setShortcut(QKeySequence(str(this_clust)))
    
    self.checked_clusts = [this_clust]
    
    if not init:
        change_cluster(self)
            
def change_cluster(self):
    self.checked_clusts = []
    for key in self.clust_buttons:
        if self.clust_buttons[key].isChecked():
            self.checked_clusts.append(key)
            
    refresh_plots(self)
    
            
def delete_cluster(self):
    start_keys = copy.deepcopy(self.clust_buttons.keys())
    for key in start_keys:
        if self.clust_buttons[key].isChecked():
            self.clusts[self.clusts == int(key)] = 0
            del self.clust_buttons[key]
            del self.cluster_dict[key]
            del self.isi_dict[key]
            
#            self.canvasisi.hist_dict[key].parent = None
            
            del self.timestamp_dict[key]
            
#            self.reinit_isi()
            
            for channel in range(len(self.waveforms)):
                del self.wave_dict[str(channel)][str(key)]
                del self.wavepoint_dict[str(channel)][str(key)]
            
    checked = []
    for key in self.clust_buttons:
        if self.clust_buttons[key].isChecked():
            checked.append(int(key))
            
    self.checked_clusts = checked
                        
    shift_clusters(self)
            
def shift_clusters(self):
    
    old_keys = []
    for key in self.clust_buttons:
        old_keys.append(int(key))
        
    sorted_keys = np.sort(old_keys)
            
    new_buttons = {}
    new_dict = {}
    new_wave_dict = {}
    new_wavepoint_dict = {}
    count = 1
    for channel in range(len(self.wave_dict)):
        new_wave_dict[str(channel)] = {}
        new_wavepoint_dict[str(channel)] = {}
        
    for key in sorted_keys:
        new_dict[str(count)] = self.cluster_dict[str(key)]
        
        for channel in range(len(self.wave_dict)):
            new_wave_dict[str(channel)][str(count)] = self.wave_dict[str(channel)][str(key)]
            new_wavepoint_dict[str(channel)][str(count)] = self.wavepoint_dict[str(channel)][str(key)]

        new_buttons[str(count)] = self.clust_buttons[str(key)]
        new_buttons[str(count)].setText(str(count))
        new_buttons[str(count)].setStyleSheet('QPushButton {background-color: %s}' % self.cs[count])
        
        
        self.clusts[self.clusts == int(key)] = int(count)
        count += 1
        
    self.clust_buttons = new_buttons
    self.cluster_dict = new_dict
    self.wave_dict = new_wave_dict
    self.wavepoint_dict = new_wavepoint_dict
    self.tot_clusts = len(self.clust_buttons)
            
    for i in reversed(range(self.clusters_layout.count())): 
        self.clusters_layout.itemAt(i).widget().setParent(None)
        
    self.clusters_layout.addWidget(self.clusters_label)
    for key in range(1,count):
        self.clusters_layout.addWidget(self.clust_buttons[str(key)])
        self.clust_buttons[str(key)].setShortcut(QKeySequence(str(key)))
        
    change_cluster(self)
        
def refresh_plots(self):
    
    self.cluster_dict[str(0)] = [index for index,value in enumerate(self.clusts) if value==0]

    self.canvaswaves.update_plots()
    self.canvas3d.update_colors()
    
    self.canvasavg.refresh_avg_waves()
    self.canvasavg.update_plots()
    
    
    self.canvasisi.refresh_times()
    self.canvasisi.update_plots()

    
def merge_clusters(self):
    
    checked = []
    for key in self.clust_buttons:
        if self.clust_buttons[key].isChecked():
            checked.append(int(key))
            
    new_clust = int(min(checked))
    new_spikes = []
    
    for key in checked:
        new_spikes += np.asarray(self.cluster_dict[str(key)]).tolist()
        if key != new_clust:
            del self.clust_buttons[str(key)]
            del self.cluster_dict[str(key)]
            del self.isi_dict[str(key)]
            
            
            
#            self.canvasisi.hist_dict[str(key)].parent = None
#            self.canvasisi.view.update()
            
            del self.timestamp_dict[str(key)]
            
            
            
            for channel in range(len(self.waveforms)):
                del self.wave_dict[str(channel)][str(key)]
                del self.wavepoint_dict[str(channel)][str(key)]
            
    self.cluster_dict[str(new_clust)] = new_spikes
    self.clusts[new_spikes] = new_clust
    
    self.cluster_dict[str(new_clust)] = [index for index, clust in enumerate(self.clusts) if clust == new_clust]

    for channel in range(len(self.waveforms)):
        new_waves = self.waveforms[channel][self.cluster_dict[str(new_clust)]]
        self.wave_dict[str(channel)][str(new_clust)] = new_waves
    
    self.checked_clusts = [new_clust]
    
    shift_clusters(self)
    
    