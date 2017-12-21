# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 12:38:03 2017

waveform cutter

@author: Patrick
"""

import numpy as np
import sort_2d
import time_plots
import avg_waves
import cluster_edit

def plot_waveforms(waveforms,self):
    
    plot = self.waveplot
    self.plot_figs['wave_view'].clear()
    
    if plot == 'all':
        subplots = [221,222,223,224]
    else:
        subplots = [0,0,0,0]
        subplots[plot-1] = 111
    
    if plot == 1 or plot == 'all':
        ax1 = self.plot_figs['wave_view'].add_subplot(subplots[0],facecolor='black')
        ax1.set_xticks([])
        ax1.set_yticks([])
        line1,=ax1.plot([],[],'r.',zorder=10)
        lines = [line1]
        axes = [ax1]
        
    if plot == 2 or plot == 'all':
        ax2 = self.plot_figs['wave_view'].add_subplot(subplots[1],facecolor='black')
        ax2.set_xticks([])
        ax2.set_yticks([])
        line2,=ax2.plot([],[],'r.',zorder=10)
        lines = [line2]
        axes = [ax2]
        
    if plot == 3 or plot == 'all':
        ax3 = self.plot_figs['wave_view'].add_subplot(subplots[2],facecolor='black')
        ax3.set_xticks([])
        ax3.set_yticks([])
        line3,=ax3.plot([],[],'r.',zorder=10)
        lines = [line3]
        axes = [ax3]
        
    if plot == 4 or plot == 'all':
        ax4 = self.plot_figs['wave_view'].add_subplot(subplots[3],facecolor='black')
        ax4.set_xticks([])
        ax4.set_yticks([])
        line4,=ax4.plot([],[],'r.',zorder=10)
        lines = [line4]
        axes = [ax4]

    if plot == 'all':
        lines=[line1,line2,line3,line4]
        axes=[ax1,ax2,ax3,ax4]
        channels = [0,1,2,3]
        for channel in channels:
            axes[channel].vlines(range(40),-1000,1000,'gray')
    else:
        channels = [plot-1]
        axes[0].vlines(range(40),-1000,1000,'gray')

    if len(self.checked_clusts) > 0:
        for channel in channels:
            for key in self.checked_clusts:
                if len(self.wave_dict[str(channel)][str(key)]) > 0:
                    nsamps = len(self.wave_dict[str(channel)][str(key)][0])
                    nchosen = len(self.wave_dict[str(channel)][str(key)][::5])
                    wave_collec = []
                    for wave in self.wave_dict[str(channel)][str(key)][::5]:
                        wave_collec += wave.tolist()
                        wave_collec.append(None)
                    x_vals = np.tile(range(nsamps+1),nchosen)
                        
                    if plot != 'all':
                        axes[0].plot(x_vals,wave_collec,color=self.cs[int(key)])
                        axes[0].set_ylim([np.min(self.wave_dict[str(channel)][str(key)])-10,np.max([self.wave_dict[str(channel)][str(key)]])+10])
                    else:
                        axes[channel].plot(x_vals,wave_collec,color=self.cs[int(key)])
                        axes[channel].set_ylim([np.min(self.wave_dict[str(channel)][str(key)])-10,np.max([self.wave_dict[str(channel)][str(key)]])+10])
          
    self.plot_figs['wave_view'].canvas.draw()
    
    self.wave_axes = axes
    self.wave_lines = lines

def on_press(self,event):

    if event.dblclick:
        if self.waveplot == 'all':
            ax = event.inaxes
            self.waveplot = self.wave_axes.index(ax)+1
            self.plot_figs['wave_view'].clear()
            plot_waveforms(self.waveforms,self)

        else:
            self.waveplot = 'all'
            self.plot_figs['wave_view'].clear()
            plot_waveforms(self.waveforms,self)
            
    else:
        x_val = event.xdata
        if isinstance(x_val,float):
            sample = np.around(x_val)
            y_val = event.ydata
            self.wave_plot = self.wave_axes.index(event.inaxes)
            if len(self.thresh_points[self.wave_plot]) == 0 or (len(self.thresh_points[self.wave_plot])>0 and sample != self.last_sample[self.wave_plot]):
                self.wave_lines[self.wave_plot].set_xdata(sample)
                self.wave_lines[self.wave_plot].set_ydata(y_val)
                self.thresh_points[self.wave_plot]=[y_val]
                self.last_sample[self.wave_plot] = sample
                self.plot_figs['wave_view'].canvas.draw_idle()
            elif len(self.thresh_points[self.wave_plot])==1 and sample == self.last_sample[self.wave_plot] and len(self.checked_clusts) == 1:
                self.wave_lines[self.wave_plot].set_xdata(sample)
                self.wave_lines[self.wave_plot].set_ydata(y_val)
                self.thresh_points[self.wave_plot].append(y_val)
                
                high = np.max(self.thresh_points[self.wave_plot])
                low = np.min(self.thresh_points[self.wave_plot])
                
                if self.waveplot == 'all':
                    #poorly named....
                    channel = self.wave_plot
                else:
                    channel = self.waveplot-1
                    
                current_clust = int(self.checked_clusts[0])
                    
                high_inds = np.where(self.wavepoints[channel][int(sample)] > low)[0]
                low_inds = np.where(self.wavepoints[channel][int(sample)] < high)[0]
                clust_inds = np.where(self.clusts == current_clust)[0]
                
                mid_inds = np.intersect1d(high_inds,low_inds)
                new_inds = np.intersect1d(mid_inds,clust_inds)
                                
                self.cluster_dict[str(current_clust)] = new_inds
                
                print self.cluster_dict.keys()
                
                self.clusts[clust_inds] = 0
                self.clusts[new_inds] = current_clust
                for i in range(len(self.waveforms)):
                    self.wave_dict[str(i)][str(current_clust)] = self.waveforms[i][new_inds]
                self.thresh_points[self.wave_plot] = []

                cluster_edit.refresh_plots(self)