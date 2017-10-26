# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 12:38:03 2017

waveform cutter

@author: Patrick
"""

import numpy as np
#import matplotlib.pyplot as plt
from OpenEphys import loadSpikes
import tkFileDialog
from matplotlib import colors as mplcolors
from matplotlib import collections  as mc

def plot_waveforms(waveforms,gui):
    
    ax1 = gui.topfigure.add_subplot(221)
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax2 = gui.topfigure.add_subplot(222)
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax3 = gui.topfigure.add_subplot(223)
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax4 = gui.topfigure.add_subplot(224)
    ax4.set_xticks([])
    ax4.set_yticks([])
    
#    collections = []
#    lc = mc.LineCollection(waveforms, colors=c, linewidths=2)
    
    line1,=ax1.plot([],[],'r.',zorder=10)
    
    axes=[ax1,ax2,ax3,ax4]
    
    for channel in range(len(waveforms)):
        nsamps = len(waveforms[channel][0])
        nchosen = len(waveforms[channel][::10])
        axes[channel].vlines(range(len(waveforms[channel][0])),-1000,1000,'gray')
#        wave_collec = mc.LineCollection(np.asarray(np.vstack((np.tile(range(len(waveforms[channel][0])),len(waveforms[channel])),waveforms[channel].flatten())).T))
#        axes[channel].add_collection(wave_collec)
        wave_collec = []
#        collections[channel] = mc.LineCollection(waveforms[channel])
        for wave in waveforms[channel][::10]:
            wave_collec += wave.tolist()
            wave_collec.append(None)
        x_vals = np.tile(range(nsamps+1),nchosen)
            
        axes[channel].plot(x_vals,wave_collec,'k-')
        axes[channel].set_ylim([np.min(waveforms[channel])-10,np.max([waveforms[channel]])+10])
        
    gui.topfigure.tight_layout()
    gui.topcanvas.draw()
        
    return axes,line1

def cut_waveforms(axes,line1,fig):
    
    def on_press(event):
        global thresh_points,last_sample,line1
        sample = np.around(event.xdata)
        y_val = event.ydata
        print event.inaxes
        if len(thresh_points) == 0 or (len(thresh_points)>0 and sample != last_sample):
            line1.set_xdata(sample)
            line1.set_ydata(y_val)
            thresh_points=[y_val]
            last_sample = sample
            fig.canvas.draw_idle()
        if len(thresh_points)==1 and sample == last_sample:
            line1.set_xdata(sample)
            line1.set_ydata(y_val)
            thresh_points = []
        
    thresh_points = []
    last_sample = 0
    fig.canvas.mpl_connect('button_press_event', on_press)