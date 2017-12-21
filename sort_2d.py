# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:44:56 2017

2d sort program

@author: Patrick
"""
import numpy as np
#import matplotlib.pyplot as plt
from OpenEphys import loadSpikes
import tkFileDialog
import wave_cut
import avg_waves
import time_plots

#import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib import path
from matplotlib import colors as mplcolors


def find_peaks(waveforms):
    peaks = np.max(waveforms,axis=2)
    peaks = np.swapaxes(peaks,0,1)
    
    return peaks

def find_valleys(waveforms):
    valleys = np.min(waveforms,axis=2)
    valleys = np.swapaxes(valleys,0,1)
    
    return valleys

def draw_plots(param,clusts,clust_colors,norm,self):
    
    plot = self.paramplot
    
    subplots = [0,0,0,0,0,0]
    if plot=='all':
        subplots = [231,232,233,234,235,236]
    else:
        subplots[plot-1] = 111
    
    if plot == 1 or plot == 'all':
        
        ax1 = self.plot_figs['param_view'].add_subplot(subplots[0])
        ax1.set_title('0x1')
        line1=ax1.scatter(param[0],param[1],c=clusts,cmap=clust_colors,norm=norm,s=.2)
        ax1.set_aspect('equal')
        if plot == 1:
            self.lines=[line1]
            self.axes=[ax1]
        
        self.points1=np.vstack((param[0],param[1])).T
        self.lasso1 = LassoSelector(ax1, lambda verts: onselect(self,verts,self.points1))
        
    if plot == 2 or plot == 'all':
        ax2 = self.plot_figs['param_view'].add_subplot(subplots[1])
        ax2.set_title('0x2')
        line2=ax2.scatter(param[0],param[2],c=clusts,cmap=clust_colors,norm=norm,s=.2)
        ax2.set_aspect('equal')
        if plot == 2:
            self.lines=[line2]
            self.axes=[ax2]
        
        self.points2=np.vstack((param[0],param[2])).T
        self.lasso2 = LassoSelector(ax2, lambda verts: onselect(self,verts,self.points2))
    
    if plot == 3 or plot == 'all':
        ax3 = self.plot_figs['param_view'].add_subplot(subplots[2])
        ax3.set_title('0x3')
        line3=ax3.scatter(param[0],param[3],c=clusts,cmap=clust_colors,norm=norm,s=.2)
        ax3.set_aspect('equal')
        if plot == 3:
            self.lines=[line3]
            self.axes=[ax3]
        
        self.points3=np.vstack((param[0],param[3])).T
        self.lasso3 = LassoSelector(ax3, lambda verts: onselect(self,verts,self.points3))
    
    if plot == 4 or plot == 'all':
        ax4 = self.plot_figs['param_view'].add_subplot(subplots[3])
        ax4.set_title('1x2')
        line4=ax4.scatter(param[1],param[2],c=clusts,cmap=clust_colors,norm=norm,s=.2)
        ax4.set_aspect('equal')
        if plot == 4:
            self.lines=[line4]
            self.axes=[ax4]
        
        self.points4=np.vstack((param[1],param[2])).T
        self.lasso4 = LassoSelector(ax4, lambda verts: onselect(self,verts,self.points4))
    
    if plot == 5 or plot == 'all':
        ax5 = self.plot_figs['param_view'].add_subplot(subplots[4])
        ax5.set_title('1x3')
        line5=ax5.scatter(param[1],param[3],c=clusts,cmap=clust_colors,norm=norm,s=.2)
        ax5.set_aspect('equal')
        if plot == 5:
            self.lines=[line5]
            self.axes=[ax5]
        
        self.points5=np.vstack((param[1],param[3])).T
        self.lasso5 = LassoSelector(ax5, lambda verts: onselect(self,verts,self.points5))
    
    if plot == 6 or plot == 'all':
        ax6 = self.plot_figs['param_view'].add_subplot(subplots[5])
        ax6.set_title('2x3')
        line6=ax6.scatter(param[2],param[3],c=clusts,cmap=clust_colors,norm=norm,s=.2)
        ax6.set_aspect('equal')
        if plot == 6:
            self.lines=[line6]
            self.axes=[ax6]
        
        self.points6=np.vstack((param[2],param[3])).T
        self.lasso6 = LassoSelector(ax6, lambda verts: onselect(self,verts,self.points6))
    
    if plot == 'all':
        self.plot_figs['param_view'].tight_layout(pad=0)
        self.lines = [line1,line2,line3,line4,line5,line6]
        self.axes = [ax1,ax2,ax3,ax4,ax5,ax6]
        
    self.plot_figs['param_view'].canvas.draw()
    
def update_colors(self):
    for line in self.lines:
        line.set_array(self.clusts)

def plot_peaks(self):
    self.param = self.peaks
    self.plot_figs['param_view'].clear()
    draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)

def plot_valleys(self):
    self.param = self.valleys
    self.plot_figs['param_view'].clear()
    draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)

def plot_energy(self):
    self.param = self.energy
    self.plot_figs['param_view'].clear()
    draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)

def on_click(self,event):
    if event.dblclick:
        if self.paramplot == 'all':
            ax = event.inaxes
            try:
                self.paramplot = self.axes.index(ax)+1
                self.plot_figs['param_view'].clear()
                draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)
            except:
                pass

        else:
            self.plot_figs['param_view'].clear()
            self.paramplot = 'all'
            draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)

    
def onselect(self,verts,points):
    if len(self.checked_clusts) == 1:
        current_clust = int(self.checked_clusts[0])
        
        print current_clust
        print self.clusts
        
        print np.where(self.clusts == 2)
        
        p = path.Path(verts)
        ind = p.contains_points(points, radius=0)
        if np.isin(current_clust,self.clusts):
            new_spikes = np.zeros(len(self.clusts),dtype=np.int)
            new_spikes = np.where(ind == True)[0]
            old_spikes = np.where(self.clusts == current_clust)[0]
            overlap = np.intersect1d(old_spikes,new_spikes)
            if len(overlap) > 0:
                self.clusts[old_spikes] = 0
                self.clusts[overlap] = current_clust
        else:
            self.clusts[ind] = current_clust
            
        update_colors(self)
        self.cluster_dict[str(current_clust)] = [index for index, clust in enumerate(self.clusts) if clust == current_clust]

        for channel in range(len(self.waveforms)):
            new_waves = self.waveforms[channel][self.cluster_dict[str(current_clust)]]
            self.wave_dict[str(channel)][str(current_clust)] = new_waves
            
        wave_cut.plot_waveforms(self.waveforms,self)

        avg_waves.refresh_avg_waves(self)
        avg_waves.plot_avg_waves(self)
        
        time_plots.refresh_times(self)
        time_plots.plot_isi(self)
        
        self.plot_figs['param_view'].canvas.draw_idle()