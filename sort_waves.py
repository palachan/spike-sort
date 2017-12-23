# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 11:48:39 2017

2d waveform sorting class

@author: Patrick
"""

import os
os.environ['QT_API'] = 'pyside'
import numpy as np
from vispy import scene
import vispy.color
import vispy.visuals
import vispy.util
from vispy.scene import visuals
import copy
import cluster_edit
from PySide import QtGui


class WaveformScene(QtGui.QWidget):
    
    def __init__(self, gui, keys='interactive', plot='all'):
        
        super(WaveformScene, self).__init__()
        
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(200,200)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        
        self.canvas.create_native()
        box.addWidget(self.canvas.native)
        
        self.canvas.events.mouse_double_click.connect(self.on_dblclick)
        self.canvas.events.mouse_press.connect(self.on_mouse_click)
        
#        self.canvas.events.mouse_move.connect(self.on_mouse_move)
#        self.canvas.events.mouse_release.connect(self.on_mouse_release)
        
        self.init_plots(plot)
        
    def init_plots(self,plot):
        
        self.plot = plot
        
        if plot == 'all':
            self.grid = self.canvas.central_widget.add_grid()
        
            self.channel1 = self.grid.add_view(row=0, col=0)
            self.channel2 = self.grid.add_view(row=0, col=1)
            self.channel3 = self.grid.add_view(row=1, col=0)
            self.channel4 = self.grid.add_view(row=1, col=1)

            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
    
            self.channel1.camera = 'panzoom'
            self.channel2.camera = 'panzoom'
            self.channel3.camera = 'panzoom'
            self.channel4.camera = 'panzoom'
            
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            self.waveline4 = visuals.Line(parent=self.channel4.scene)
            
            self.thresh_points1 = visuals.Markers(parent=self.channel1.scene)
            self.thresh_points2 = visuals.Markers(parent=self.channel2.scene)
            self.thresh_points3 = visuals.Markers(parent=self.channel3.scene)
            self.thresh_points4 = visuals.Markers(parent=self.channel4.scene)
            
        elif plot == 1:
            self.channel1 = self.canvas.central_widget.add_view()

            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            self.channel1.camera = 'panzoom'
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            self.thresh_points1 = visuals.Markers(parent=self.channel1.scene)
            
            self.last_plot = self.channel1
            
        elif plot == 2:
            self.channel2 = self.canvas.central_widget.add_view()

            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            self.channel2.camera = 'panzoom'
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            self.thresh_points2 = visuals.Markers(parent=self.channel2.scene)
            
            self.last_plot = self.channel2
            
        elif plot == 3:
            self.channel3 = self.canvas.central_widget.add_view()

            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            self.channel3.camera = 'panzoom'
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            self.thresh_points3 = visuals.Markers(parent=self.channel3.scene)
            
            self.last_plot = self.channel3
            
        elif plot == 4:
            self.channel4 = self.canvas.central_widget.add_view()

            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
            self.channel4.camera = 'panzoom'
            self.waveline4 = visuals.Line(parent=self.channel4.scene)
            self.thresh_points4 = visuals.Markers(parent=self.channel4.scene)
            
            self.last_plot = self.channel4
            
        self.thresh_points = [[],[],[],[]]
        self.last_sample = [-100,-100,-100,-100]
        
        self.update_plots()
        
    def update_plots(self):
        
        if self.plot == 'all':
            channel_list = [0,1,2,3]
        elif self.plot == 1:
            channel_list = [0]
        elif self.plot == 2:
            channel_list = [1]
        elif self.plot == 3:
            channel_list = [2]
        elif self.plot == 4:
            channel_list = [3]
        
        checked_clusts = []
        
        for i in range(len(self.gui.waveforms)):
            self.gui.wave_dict[str(i)][str(0)] = self.gui.waveforms[i][np.asarray(self.gui.cluster_dict[str(0)],dtype=np.int)]
        
        if len(self.gui.checked_clusts) == 0:
            checked_clusts = []
            
        else:
            for i in range(len(self.gui.waveforms)):
                for key in self.gui.checked_clusts:
                    if len(self.gui.cluster_dict[str(key)]) > 0:
                        checked_clusts.append(key)
                        self.gui.wave_dict[str(i)][str(key)] = self.gui.waveforms[i][np.asarray(self.gui.cluster_dict[str(key)],dtype=np.int)]

        if len(checked_clusts) == 0:
            checked_clusts = [0]


    
        for channel in [0,1,2,3]:
            colors = []
            wave_collec = []
            x_vals = []
            for key in checked_clusts:
                max_points = 1000.
                step = int(np.ceil(float(len(self.gui.wave_dict[str(channel)][str(key)]))/max_points))
                if len(self.gui.wave_dict[str(channel)][str(key)]) > 0:
                    nsamps = len(self.gui.wave_dict[str(channel)][str(key)][0])
                    for wave in self.gui.wave_dict[str(channel)][str(key)][::step]:
                        wave_collec += wave.tolist()
                        
                        color = copy.deepcopy(self.gui.canvas3d.color_ops[int(key)])
                        if int(key) != 0:
                            color[3] = .8
                        for i in range(len(wave)):
                            colors.append(color)
                        wave_collec.append(None)
                        colors.append([0,0,0,0])
                        
                    x_vals_now = np.tile(range(-8,nsamps-7),len(self.gui.wave_dict[str(channel)][str(key)][::step])).tolist()
                    x_vals += x_vals_now
            
            colors = np.asarray(colors)
#                x_vals = np.asarray(x_vals)
            pos = np.swapaxes(np.vstack((x_vals,wave_collec)),0,1)
            
            if channel in channel_list:
            
                if channel==0:
                    self.waveline1.set_data(pos,color=colors)
                    self.channel1.camera.rect = -8,1.2*np.nanmin(np.array(wave_collec,dtype=np.float)),40,1.2*np.nanmax(np.array(wave_collec,dtype=np.float))-1.2*np.nanmin(np.array(wave_collec,dtype=np.float))
                elif channel==1:
                    self.waveline2.set_data(pos,color=colors)
                    self.channel2.camera.rect = -8,1.2*np.nanmin(np.array(wave_collec,dtype=np.float)),40,1.2*np.nanmax(np.array(wave_collec,dtype=np.float))-1.2*np.nanmin(np.array(wave_collec,dtype=np.float))
                elif channel==2:
                    self.waveline3.set_data(pos,color=colors)
                    self.channel3.camera.rect = -8,1.2*np.nanmin(np.array(wave_collec,dtype=np.float)),40,1.2*np.nanmax(np.array(wave_collec,dtype=np.float))-1.2*np.nanmin(np.array(wave_collec,dtype=np.float))
                elif channel==3:
                    self.waveline4.set_data(pos,color=colors)
                    self.channel4.camera.rect = -8,1.2*np.nanmin(np.array(wave_collec,dtype=np.float)),40,1.2*np.nanmax(np.array(wave_collec,dtype=np.float))-1.2*np.nanmin(np.array(wave_collec,dtype=np.float))

        
    def on_dblclick(self, event):
        
        if event.button == 1:
            viewbox = self.canvas.visual_at(event.pos)
            
            if self.plot == 'all':
                
                self.grid.parent = None
#                self.init_plots(plot)
            
                if viewbox == self.channel1:
                    self.init_plots(1)
                elif viewbox == self.channel2:
                    self.init_plots(2)
                elif viewbox == self.channel3:
                    self.init_plots(3)
                elif viewbox == self.channel4:
                    self.init_plots(4)
                    
            else:
                self.last_plot.parent = None
                self.init_plots('all')
                
    def on_mouse_click(self, event):
        
        if event.button == 1 and vispy.util.keys.CONTROL in event.modifiers:
            
            viewbox = self.canvas.visual_at(event.pos)
            
            if self.plot == 'all':
                if viewbox == self.channel1:
                    channel = 0
                elif viewbox == self.channel2:
                    channel = 1
                elif viewbox == self.channel3:
                    channel = 2
                elif viewbox == self.channel4:
                    channel = 3
                    
            else:
                channel = self.plot - 1
                
            if channel == 0:
                thresh_collec = self.thresh_points1
            elif channel == 1:
                thresh_collec = self.thresh_points2
            elif channel == 2:
                thresh_collec = self.thresh_points3
            elif channel == 3:
                thresh_collec = self.thresh_points4
                
            if self.plot == 'all':
                x_val,y_val = viewbox.scene.transform.imap(viewbox.transform.imap(event.pos))[0:2]

            else:
                x_val,y_val = viewbox.scene.transform.imap(event.pos)[0:2]

            sample = np.around(x_val)

            if len(self.thresh_points[channel]) == 0 or (len(self.thresh_points[channel])>0 and sample != self.last_sample[channel]):
                thresh_collec.set_data(pos=np.asarray([[sample,y_val]]),face_color='red')
                
                self.thresh_points[channel]=[y_val]
                self.last_sample[channel] = sample
                
            elif len(self.thresh_points[channel])==1 and sample == self.last_sample[channel] and len(self.gui.checked_clusts) == 1:

                self.thresh_points[channel].append(y_val)
                thresh_collec.set_data(pos=np.asarray([[sample,y_val],[sample,self.thresh_points[channel][0]]]),face_color='red')
                
                high = np.max(self.thresh_points[channel])
                low = np.min(self.thresh_points[channel])

                current_clust = int(self.gui.checked_clusts[0])
                                    
                high_inds = np.where(self.gui.wavepoints[channel][int(sample+8)] > low)[0]
                low_inds = np.where(self.gui.wavepoints[channel][int(sample+8)] < high)[0]
                clust_inds = np.where(self.gui.clusts == current_clust)[0]
                
                mid_inds = np.intersect1d(high_inds,low_inds)
                new_inds = np.intersect1d(mid_inds,clust_inds)
                                
                self.gui.cluster_dict[str(current_clust)] = new_inds
                                
                self.gui.clusts[clust_inds] = 0
                self.gui.clusts[new_inds] = current_clust
                for i in range(len(self.gui.waveforms)):
                    self.gui.wave_dict[str(i)][str(current_clust)] = self.gui.waveforms[i][new_inds]
                self.thresh_points[channel] = []
                
                self.gui.lratios[str(self.gui.checked_clusts[0])],self.gui.iso_dists[str(self.gui.checked_clusts[0])] = cluster_edit.calc_l_ratio(self.gui.all_points,self.gui.cluster_dict[str(self.gui.checked_clusts[0])])
    
                cluster_edit.shift_clusters(self.gui)
