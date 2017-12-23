# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 11:09:38 2017

handles cluster stuff, like adding, deleting, merging, etc.

@author: Patrick
"""

import copy
import numpy as np
import numba as nb
import time
from scipy.stats import chi2
from PySide.QtGui import QPushButton,QKeySequence,QLabel

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
    
    self.clust_labels[str(this_clust)] = None
    
    self.checked_clusts = [this_clust]
    
    if not init:
        self.lratios[str(this_clust)],self.iso_dists[str(this_clust)] = [np.nan,np.nan]
    else:
        self.lratios[str(this_clust)],self.iso_dists[str(this_clust)] = calc_l_ratio(self.all_points,self.cluster_dict[str(this_clust)])
    
    if not init:
        change_cluster(self)
            
def change_cluster(self):
    
    self.checked_clusts = []
    for key in self.clust_buttons:
        if self.clust_buttons[key].isChecked():
            self.checked_clusts.append(key)

    for key in self.clust_labels:
        if self.clust_labels[key] is not None and key not in self.checked_clusts:
            self.clust_labels[key].setText('')
            self.params_layout.removeWidget(self.clust_labels[key])
            self.clust_labels[key] = None
        elif self.clust_labels[key] is not None and key in self.checked_clusts:
            self.clust_labels[key].setText('Cluster %s: %d spikes \n Lratio: %f \n Iso Dist: %f' % (key,len(self.cluster_dict[key]),self.lratios[key],self.iso_dists[key]))
        elif self.clust_labels[key] is None and key in self.checked_clusts:
            self.clust_labels[key] = QLabel('Cluster %s: %d spikes \n Lratio: %f \n Iso Dist: %f' % (key,len(self.cluster_dict[key]),self.lratios[key],self.iso_dists[key]))
            self.params_layout.addWidget(self.clust_labels[key])
            
    refresh_plots(self)
    
            
def delete_cluster(self):
    start_keys = copy.deepcopy(self.clust_buttons.keys())
    for key in start_keys:
        if self.clust_buttons[key].isChecked():
            self.clusts[self.clusts == int(key)] = 0
            del self.clust_buttons[key]
            del self.cluster_dict[key]
            del self.isi_dict[key]
            
            if self.clust_labels[str(key)] is not None:
                self.params_layout.removeWidget(self.clust_labels[str(key)])
                
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
            
            del self.timestamp_dict[str(key)]
            
            if self.clust_labels[str(key)] is not None:
                self.params_layout.removeWidget(self.clust_labels[str(key)])
            
            for channel in range(len(self.waveforms)):
                del self.wave_dict[str(channel)][str(key)]
                del self.wavepoint_dict[str(channel)][str(key)]
            
    self.cluster_dict[str(new_clust)] = new_spikes
    self.clusts[new_spikes] = new_clust
    
    self.cluster_dict[str(new_clust)] = [index for index, clust in enumerate(self.clusts) if clust == new_clust]

    self.lratios[str(new_clust)],self.iso_dists[str(new_clust)] = calc_l_ratio(self.all_points,self.cluster_dict[str(new_clust)])


    for channel in range(len(self.waveforms)):
        new_waves = self.waveforms[channel][self.cluster_dict[str(new_clust)]]
        self.wave_dict[str(channel)][str(new_clust)] = new_waves
    
    self.checked_clusts = [new_clust]
    
    shift_clusters(self)
    
def calc_l_ratio(all_points,clust_inds):
          
    points = all_points[:,clust_inds]
    mean_points = np.mean(np.swapaxes(points,0,1),axis=0)
    cov_matrix = np.cov(points)
        
    #use SVD to get inverse of covariance matrix in case it's too singular (which
    #will happen if we have shorted wires and the corresponding features are identical)
    u,s,v = np.linalg.svd(cov_matrix)
    invcov = np.dot(np.dot(v.T,np.linalg.inv(np.diagflat(s))),u.T)

    other_points = np.swapaxes(np.delete(all_points,clust_inds,axis=1),0,1)
    
    noise_dists = np.zeros(len(other_points),dtype=np.float)
        
    for i in range(len(other_points)):
        diff = other_points[i] - mean_points
        
        mdist = np.dot(np.dot(diff.T,invcov),diff)
        noise_dists[i] = np.float(mdist)

    noise_dists = np.sort(noise_dists)
    lratio = np.sum(chi2.sf(noise_dists,df=8))/len(clust_inds)

    if len(noise_dists) > len(clust_inds):
        iso_distance = noise_dists[len(clust_inds)-1]
    else:
        iso_distance = np.nan
        

    
    return lratio,iso_distance
        
    
    
    
    