# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 11:09:38 2017

handles cluster stuff, like adding, deleting, merging, etc.

@author: Patrick
"""

import copy
import numpy as np
from PySide.QtGui import QPushButton
import sort_2d
import wave_cut
import avg_waves
import time_plots

def new_cluster(self):
    self.tot_clusts += 1
    this_clust = int(copy.deepcopy(self.tot_clusts))
    if this_clust < 10:
        print this_clust
        self.clust_buttons[str(this_clust)] = QPushButton('&'+str(this_clust))
    else:
        self.clust_buttons[str(this_clust)] = QPushButton(str(this_clust))
    self.clust_buttons[str(this_clust)].setCheckable(True)
    self.clust_buttons[str(this_clust)].setStyleSheet('QPushButton {background-color: %s}' % self.cs[this_clust])
    self.clusters_layout.addWidget(self.clust_buttons[str(this_clust)])
    
    self.cluster_dict[str(this_clust)] = []
    
    for channel in range(len(self.waveforms)):
        self.wave_dict[str(channel)][str(this_clust)] = []
        self.wavepoint_dict[str(channel)][str(this_clust)] = []
    
    for key in self.clust_buttons:
        self.clust_buttons[key].setChecked(False)
    self.clust_buttons[str(this_clust)].setChecked(True)
    self.clust_buttons[str(this_clust)].toggled.connect(lambda: change_cluster(self))
    self.checked_clusts = [this_clust]
            
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
            del self.timestamp_dict[key]
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
        
    refresh_plots(self)
        
def refresh_plots(self):
            
#    self.plot_figs['param_view'].clear()
    self.plot_figs['wave_view'].clear()
    self.plot_figs['avg_wave'].clear()
    self.plot_figs['isi_hist'].clear()
    
    sort_2d.update_colors(self)
    self.plot_figs['param_view'].canvas.draw_idle()
    
    wave_cut.plot_waveforms(self.waveforms,self)
    
    avg_waves.refresh_avg_waves(self)
    avg_waves.plot_avg_waves(self)
    
    time_plots.refresh_times(self)
    time_plots.plot_isi(self)
    
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
    
    