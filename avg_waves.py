# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 09:46:59 2017

average waveform plot

@author: Patrick
"""            
            
import os
os.environ['QT_API'] = 'pyside'
import numpy as np
from vispy import scene
from vispy.scene import visuals
from PySide import QtGui


class AvgWaveformScene(QtGui.QWidget):
    
    def __init__(self, gui, keys='interactive', plot='all'):
        
        super(AvgWaveformScene, self).__init__()
        
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(200,200)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        
        self.canvas.create_native()
        box.addWidget(self.canvas.native)
        
        self.poly_dict = {}
        for i in range(4):
            self.poly_dict[str(i)] = {}
        
        self.canvas.events.mouse_double_click.connect(self.on_dblclick)
        
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

        elif plot == 1:
            self.channel1 = self.canvas.central_widget.add_view()

            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            self.channel1.camera = 'panzoom'
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            
            self.last_plot = self.channel1
            
        elif plot == 2:
            self.channel2 = self.canvas.central_widget.add_view()

            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            self.channel2.camera = 'panzoom'
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            
            self.last_plot = self.channel2
            
        elif plot == 3:
            self.channel3 = self.canvas.central_widget.add_view()

            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            self.channel3.camera = 'panzoom'
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            
            self.last_plot = self.channel3
            
        elif plot == 4:
            self.channel4 = self.canvas.central_widget.add_view()

            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
            self.channel4.camera = 'panzoom'
            self.waveline4 = visuals.Line(parent=self.channel4.scene)
            
            self.last_plot = self.channel4
            
        self.refresh_avg_waves()
        self.update_plots()
        
    def refresh_avg_waves(self):
        
        self.avg_colors = [[],[],[],[]]
        
        for channel in range(len(self.gui.waveforms)):
            for key in self.gui.wave_dict[str(channel)].keys():
                if len(self.gui.wave_dict[str(channel)][key]) > 0:
                    self.gui.wave_sem_dict[str(channel)][key] = np.std(self.gui.wave_dict[str(channel)][key],axis=0)
                    self.gui.avg_wave_dict[str(channel)][key] = np.mean(self.gui.wave_dict[str(channel)][key],axis=0)
                    
                else:
                    self.gui.avg_wave_dict[str(channel)][key] = []
                    self.gui.wave_sem_dict[str(channel)][key] = []
        
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

        if len(self.gui.checked_clusts) == 0:
            checked_clusts = [0]
        else:
            checked_clusts = self.gui.checked_clusts
            
        all_empty = True
        for clust in checked_clusts:
            if len(self.gui.cluster_dict[str(clust)]) > 0:
                all_empty = False
                
        if all_empty:
            checked_clusts = [0]
            
        for i in range(4):
            for key in self.poly_dict[str(i)].keys():
                self.poly_dict[str(i)][key].parent = None

        for channel in [0,1,2,3]:
            
            colors = []
            wave_collec = []
            sem_colors = []
            x_vals = []
            
            sem_maxs = []
            sem_mins = []
            for key in checked_clusts:
                if len(self.gui.wave_dict[str(channel)][str(key)]) > 0:
                    
                    sem_collec = []
                    sem_x_vals = []
                    
                    nsamps = len(self.gui.wave_dict[str(channel)][str(key)][0])
                    wave_collec += self.gui.avg_wave_dict[str(channel)][str(key)].tolist()
                    wave_collec.append(None)
                    
                    high_sem = (self.gui.avg_wave_dict[str(channel)][str(key)] + self.gui.wave_sem_dict[str(channel)][str(key)]).tolist()
                    low_sem = (self.gui.avg_wave_dict[str(channel)][str(key)] - self.gui.wave_sem_dict[str(channel)][str(key)]).tolist()
                    
                    sem_collec += high_sem
                    sem_collec += low_sem[::-1]
                    
                    for i in range(nsamps):
                        colors.append(self.gui.canvas3d.color_ops[int(key)])
                        sem_colors.append(self.gui.canvas3d.color_ops[int(key)])
                        
                    colors.append([0,0,0,0])
                    
                    for i in range(nsamps):
                        sem_colors.append(self.gui.canvas3d.color_ops[int(key)])
                    
                    x_vals += range(-8,nsamps-7)
                    
                    sem_x_vals += range(-8,nsamps-8)
                    sem_x_vals += range(-8,nsamps-8)[::-1]
                    
                    sem_maxs.append(np.max(sem_collec))
                    sem_mins.append(np.min(sem_collec))
                    
                    sem_pos = np.swapaxes(np.vstack((sem_x_vals,sem_collec)),0,1)
                    
                    if channel==0:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel1.scene)
                    if channel==1:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel2.scene)
                    if channel==2:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel3.scene)
                    if channel==3:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel4.scene)

            pos = np.swapaxes(np.vstack((x_vals,wave_collec)),0,1)
            
            if channel in channel_list:
                
                if len(colors) > 0:
                    colors = np.asarray(colors)
                    colors[:,3] = 1
                else:
                    colors.append([0,0,0,0])
                
                if channel==0:
                    self.waveline1.set_data(pos,color=colors,width=2)
                    self.channel1.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-np.min(sem_mins)
                elif channel==1:
                    self.waveline2.set_data(pos,color=colors,width=2)
                    self.channel2.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-np.min(sem_mins)
                elif channel==2:
                    self.waveline3.set_data(pos,color=colors,width=2)
                    self.channel3.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-np.min(sem_mins)
                elif channel==3:
                    self.waveline4.set_data(pos,color=colors,width=2)
                    self.channel4.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-np.min(sem_mins)
        
    def on_dblclick(self, event):
        
        if event.button == 1:
            viewbox = self.canvas.visual_at(event.pos)
            
            if self.plot == 'all':
                
                self.grid.parent = None
            
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
            