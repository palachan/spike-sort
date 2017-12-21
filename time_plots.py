# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 10:28:22 2017

time view, isi hist, autocorr

@author: Patrick
"""
import numpy as np
import matplotlib as mpl
mpl.rcParams['backend.qt4']='PySide'
mpl.use('Qt4Agg')
import matplotlib.pyplot as plt


def refresh_times(self):
        
    for key in self.cluster_dict.keys():
        if len(self.cluster_dict[key]) > 0:
            spike_timestamps = self.timestamps[self.cluster_dict[key]]
            self.isi_dict[key] = []
            for i in range(len(spike_timestamps)-1):
                self.isi_dict[key].append(spike_timestamps[i+1]-spike_timestamps[i])
            self.timestamp_dict[key] = spike_timestamps

        else:
            self.timestamp_dict[key] = []
            self.isi_dict[key] = []
            
def plot_isi(self):
    
    self.plot_figs['isi_hist'].clear()

    ax = self.plot_figs['isi_hist'].add_subplot(111,facecolor='black')
    
    for clust in self.checked_clusts:
        clust = int(clust)
        #make a histogram of the isi's
        if len(self.isi_dict[str(clust)]) > 0:
            isi_hist = np.histogram(self.isi_dict[str(clust)],bins=50,range=[0,100000])
            isi_xvals = np.arange(0,100000,100000./50.)
            ax.vlines(isi_xvals,0,isi_hist[0],self.cs[int(str(clust))])
            
    self.plot_figs['isi_hist'].tight_layout()     
    self.plot_figs['isi_hist'].canvas.draw()
    
def plot_time(self):
    
    plt.figure(facecolor='black')
    
    plt.scatter(self.timestamps,self.param[0],c=self.clusts,cmap=self.clust_colors,norm=self.norm,s=.2)
    
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.show()