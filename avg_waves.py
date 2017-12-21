# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 09:46:59 2017

average waveform plot

@author: Patrick
"""

import numpy as np
from scipy.stats import sem

def refresh_avg_waves(self):
    
    for channel in range(len(self.waveforms)):
        for key in self.wave_dict[str(channel)].keys():
            if len(self.wave_dict[str(channel)][key]) > 0:
                self.wave_sem_dict[str(channel)][key] = np.std(self.wave_dict[str(channel)][key],axis=0)
                self.avg_wave_dict[str(channel)][key] = np.mean(self.wave_dict[str(channel)][key],axis=0)
            else:
                self.avg_wave_dict[str(channel)][key] = []
                self.wave_sem_dict[str(channel)][key] = []
                
def plot_avg_waves(self):
    
    plot = self.avgplot
    self.plot_figs['avg_wave'].clear()
    
    if self.avgplot == 'all':
        subplots = [221,222,223,224]
    else:
        subplots = [0,0,0,0]
        subplots[plot-1] = 111
    
    if plot == 1 or plot == 'all':
        ax1 = self.plot_figs['avg_wave'].add_subplot(subplots[0],facecolor='black')
        ax1.set_xticks([])
        ax1.set_yticks([])
        axes = [ax1]
        
    if plot == 2 or plot == 'all':
        ax2 = self.plot_figs['avg_wave'].add_subplot(subplots[1],facecolor='black')
        ax2.set_xticks([])
        ax2.set_yticks([])
        axes = [ax2]
        
    if plot == 3 or plot == 'all':
        ax3 = self.plot_figs['avg_wave'].add_subplot(subplots[2],facecolor='black')
        ax3.set_xticks([])
        ax3.set_yticks([])
        axes = [ax3]
        
    if plot == 4 or plot == 'all':
        ax4 = self.plot_figs['avg_wave'].add_subplot(subplots[3],facecolor='black')
        ax4.set_xticks([])
        ax4.set_yticks([])
        axes = [ax4]
        
    if plot == 'all':
        axes=[ax1,ax2,ax3,ax4]
        channels = range(len(self.waveforms))
        for channel in channels:
            axes[channel].vlines(range(40),-1000,1000,'gray')
    else:
        channels = [plot-1]
        axes[0].vlines(range(40),-1000,1000,'gray')

    if len(self.checked_clusts) > 0:
        for channel in channels:
            for key in self.checked_clusts:
                if len(self.avg_wave_dict[str(channel)][str(key)]) > 0:
                    nsamps = len(self.wave_dict[str(channel)][str(key)][0])
                        
                    if plot != 'all':
                        axes[0].errorbar(range(nsamps),self.avg_wave_dict[str(channel)][str(key)],self.wave_sem_dict[str(channel)][str(key)],color=self.cs[int(key)])
                        axes[0].set_ylim([np.min(self.wave_dict[str(channel)][str(key)])-10,np.max([self.wave_dict[str(channel)][str(key)]])+10])
                    else:
                        axes[channel].errorbar(range(nsamps),self.avg_wave_dict[str(channel)][str(key)],self.wave_sem_dict[str(channel)][str(key)],color=self.cs[int(key)])
                        axes[channel].set_ylim([np.min(self.wave_dict[str(channel)][str(key)])-10,np.max([self.wave_dict[str(channel)][str(key)]])+10])
          
    self.plot_figs['avg_wave'].tight_layout()
    self.plot_figs['avg_wave'].canvas.draw()
    
    self.avg_axes = axes
        
def on_click(self,event):

    if event.dblclick:
        if self.avgplot == 'all':
            ax = event.inaxes
            self.avgplot = self.avg_axes.index(ax)+1
            self.plot_figs['avg_wave'].clear()
            plot_avg_waves(self)

        else:
            self.avgplot = 'all'
            self.plot_figs['avg_wave'].clear()
            plot_avg_waves(self)
        