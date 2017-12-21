# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 16:19:45 2017

administrative stuff

@author: Patrick
"""

from OpenEphys import loadSpikes
import numpy as np
import os
import sort_2d
import wave_cut
import avg_waves
import cluster_edit
from PySide.QtGui import QFileDialog

def open_file(self):
    self.fname = QFileDialog.getOpenFileName(self, 'Open Spike File', '','Openephys spike files (*.spikes)')
    spike_data = loadSpikes(self.fname[0])
    
    sample_nums = spike_data['timestamps']
    self.framerate = spike_data['header']['sampleRate']
    #get timestamps in microseconds
    self.timestamps = sample_nums*1000000/self.framerate
    #norm so they start at 0
    self.timestamps = self.timestamps - np.min(self.timestamps)
    
    waveforms = np.swapaxes(spike_data['spikes'],1,2)
    self.peaks = sort_2d.find_peaks(waveforms)
    self.valleys = sort_2d.find_valleys(waveforms)
    self.energy = self.peaks**2
    
    self.num_spikes = len(waveforms)
    self.wavepoints = np.swapaxes(spike_data['spikes'],0,2)
    self.waveforms = np.swapaxes(waveforms,0,1)
    self.canvas_label.setText('2d parameters')
    self.canvas_label_top.setText('waveforms')
    self.canvas_label_mid.setText('average waveforms')
    self.canvas_label_low.setText('isi histogram')
    
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
    
    self.checked_clusts = []
    self.tot_clusts = 0
    self.clusts = np.zeros(self.num_spikes,dtype=np.int)
    self.thresh_points = [[],[],[],[]]
    self.last_sample = [0,0,0,0]

    self.waveplot = 'all'
    self.paramplot = 'all'
    self.avgplot = 'all'
    
    self.param = self.peaks
    
    sort_2d.draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)
    cluster_edit.refresh_plots()
    
    self.main_cid = self.plot_figs['param_view'].canvas.mpl_connect('button_press_event', lambda event: sort_2d.on_click(self,event))
    self.top_cid = self.plot_figs['wave_view'].canvas.mpl_connect('button_press_event', lambda event: wave_cut.on_press(self,event))
    self.mid_cid = self.plot_figs['avg_wave'].canvas.mpl_connect('button_press_event', lambda event: avg_waves.on_click(self,event))
    self.low_cid = None
    print self.main_cid
    
def save_ts(self):
    
    trodefile = os.basename(self.fname[0])
    save_dir = os.dirname(self.fname[0])
    
    for key in self.timestamp_dict.keys():
        if int(key) < 10:
            cname = '0' + key
        else:
            cname = key
        ts_file = open(save_dir + '/' + trodefile[:4]+'_SS'+cname+'.txt', 'w')
        for ts in self.timestamp_dict[key]:
            ts_file.write("%s\n" % ts)
        
        
        
        
        