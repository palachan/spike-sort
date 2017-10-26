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

def plot_it(param,num_spikes,gui):
    cs=['xkcd:grey','xkcd:red','xkcd:beige','xkcd:green','xkcd:sky blue','xkcd:pink','xkcd:lime green','xkcd:magenta']
    clust_colors = mplcolors.ListedColormap(cs)
    norm=mplcolors.Normalize(vmin=0,vmax=len(cs)-1)
    
    gui.lines,gui.axes=draw_plots(param,gui.clusts,clust_colors,norm,gui)
        
    gui.points1=np.vstack((param[0],param[1])).T
    gui.points2=np.vstack((param[0],param[2])).T
    gui.points3=np.vstack((param[0],param[3])).T
    gui.points4=np.vstack((param[1],param[2])).T
    gui.points5=np.vstack((param[1],param[3])).T
    gui.points6=np.vstack((param[2],param[3])).T
    
    gui.lasso1 = LassoSelector(gui.axes[0], gui.onselect1)
    gui.lasso2 = LassoSelector(gui.axes[1], gui.onselect2)
    gui.lasso3 = LassoSelector(gui.axes[2], gui.onselect3)
    gui.lasso4 = LassoSelector(gui.axes[3], gui.onselect4)
    gui.lasso5 = LassoSelector(gui.axes[4], gui.onselect5)
    gui.lasso6 = LassoSelector(gui.axes[5], gui.onselect6)

def draw_plots(param,clusts,clust_colors,norm,gui):
    
    ax1 = gui.mainfigure.add_subplot(231)
    ax1.set_title('0x1')
    line1=ax1.scatter(param[0],param[1],c=clusts,cmap=clust_colors,norm=norm,s=.2)
    ax1.set_aspect('equal')
    
    ax2 = gui.mainfigure.add_subplot(232)
    ax2.set_title('0x2')
    line2=ax2.scatter(param[0],param[2],c=clusts,cmap=clust_colors,norm=norm,s=.2)
    ax2.set_aspect('equal')
    
    ax3 = gui.mainfigure.add_subplot(233)
    ax3.set_title('0x3')
    line3=ax3.scatter(param[0],param[3],c=clusts,cmap=clust_colors,norm=norm,s=.2)
    ax3.set_aspect('equal')
    
    ax4 = gui.mainfigure.add_subplot(234)
    ax4.set_title('1x2')
    line4=ax4.scatter(param[1],param[2],c=clusts,cmap=clust_colors,norm=norm,s=.2)
    ax4.set_aspect('equal')
    
    ax5 = gui.mainfigure.add_subplot(235)
    ax5.set_title('1x3')
    line5=ax5.scatter(param[1],param[3],c=clusts,cmap=clust_colors,norm=norm,s=.2)
    ax5.set_aspect('equal')
    
    ax6 = gui.mainfigure.add_subplot(236)
    ax6.set_title('2x3')
    line6=ax6.scatter(param[2],param[3],c=clusts,cmap=clust_colors,norm=norm,s=.2)
    ax6.set_aspect('equal')
    
    gui.mainfigure.tight_layout()
    gui.maincanvas.draw()
    
    lines = [line1,line2,line3,line4,line5,line6]
    axes = [ax1,ax2,ax3,ax4,ax5,ax6]
    
    return lines,axes

def update_colors(lines,colors):
    for line in lines:
        line.set_array(colors)
        
    return lines

