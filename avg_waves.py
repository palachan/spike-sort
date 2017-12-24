# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 09:46:59 2017

average waveform plot

@author: Patrick
"""            
            
#import necessary modules
import numpy as np
from vispy import scene
from vispy.scene import visuals
from PySide import QtGui


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class AvgWaveformScene(QtGui.QWidget):
    ''' class for plotting average waveforms '''
    
    def __init__(self, gui, keys='interactive', plot='all'):
        #initialize
        super(AvgWaveformScene, self).__init__()
        #reference to main GUI instance
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(200,200)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        box.addWidget(self.canvas.native)
        
        #create a dict for holding SEM polygons
        self.poly_dict = {}
        #make a dict entry for each channel
        for channel in range(self.gui.num_channels):
            self.poly_dict[str(channel)] = {}
        
        #connect click events to appropriate function
        self.canvas.events.mouse_double_click.connect(self.on_dblclick)
        
        #initialize the plots
        self.init_plots(plot)
        
    def init_plots(self,plot):
        ''' creates the plotting scene '''
        
        #grab the plot we're trying to make (default all 4 channels)
        self.plot = plot
        
        #if we're plotting all channels...
        if plot == 'all':
            #add a grid to the plot
            self.grid = self.canvas.central_widget.add_grid()
            
            #add a view for each channel
            self.channel1 = self.grid.add_view(row=0, col=0)
            self.channel2 = self.grid.add_view(row=0, col=1)
            self.channel3 = self.grid.add_view(row=1, col=0)
            self.channel4 = self.grid.add_view(row=1, col=1)

            #add gridlines to each channel's plot
            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
    
            #add a PanZoom camera to each view
            self.channel1.camera = 'panzoom'
            self.channel2.camera = 'panzoom'
            self.channel3.camera = 'panzoom'
            self.channel4.camera = 'panzoom'
            
            #create a Line visual for plotting each average waveform
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            self.waveline4 = visuals.Line(parent=self.channel4.scene)

        #if we're just plotting channel 1, do that
        elif plot == 1:
            self.channel1 = self.canvas.central_widget.add_view()

            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            self.channel1.camera = 'panzoom'
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel1
            
        #if we're just plotting channel 2, do that
        elif plot == 2:
            self.channel2 = self.canvas.central_widget.add_view()

            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            self.channel2.camera = 'panzoom'
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel2
            
        #if we're just plotting channel 3, do that
        elif plot == 3:
            self.channel3 = self.canvas.central_widget.add_view()

            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            self.channel3.camera = 'panzoom'
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel3
            
        #if we're just plotting channel 4, do that
        elif plot == 4:
            self.channel4 = self.canvas.central_widget.add_view()

            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
            self.channel4.camera = 'panzoom'
            self.waveline4 = visuals.Line(parent=self.channel4.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel4
            
        #calc our average waveforms
        self.refresh_avg_waves()
        #update the plots
        self.update_plots()
        
    def refresh_avg_waves(self):
        ''' calculates an average waveform for each cluster '''
        
        #create lists to hold waveform colors
        self.avg_colors = [[],[],[],[]]
        
        #for each channel...
        for channel in range(self.gui.num_channels):
            #for each cluster, if it has spikes...
            for key in self.gui.wave_dict[str(channel)].keys():
                if len(self.gui.wave_dict[str(channel)][key]) > 0:
                    #calc the average waveform and SEMs for the cluster, add to associated dicts
                    self.gui.wave_sem_dict[str(channel)][key] = np.std(self.gui.wave_dict[str(channel)][key],axis=0)
                    self.gui.avg_wave_dict[str(channel)][key] = np.mean(self.gui.wave_dict[str(channel)][key],axis=0)
                #otherwise make empty entries
                else:
                    self.gui.avg_wave_dict[str(channel)][key] = []
                    self.gui.wave_sem_dict[str(channel)][key] = []
        
    def update_plots(self):
        ''' updat the plots with the latest data '''
        
        #figure out which channels we're plotting
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

        #if no clusters selected, we'll plot unclassified spikes
        if len(self.gui.checked_clusts) == 0:
            checked_clusts = [0]
        #otherwise, check if any of the selected clusters have spikes
        else:
            checked_clusts = self.gui.checked_clusts
            all_empty = True
            for clust in checked_clusts:
                if len(self.gui.cluster_dict[str(clust)]) > 0:
                    all_empty = False
            #if they don't have spikes, we'll plot unclassified spikes
            if all_empty:
                checked_clusts = [0]
            
        #make all the SEM polygons parentless to clear the plot
        for i in range(self.gui.num_channels):
            for key in self.poly_dict[str(i)].keys():
                self.poly_dict[str(i)][key].parent = None

        #for each channel
        for channel in channel_list:
            
            #make lists for colors and wave lines
            colors = []
            wave_collec = []
            sem_colors = []
            x_vals = []
            
            #also for keeping track of max and min values to set camera bounds
            sem_maxs = []
            sem_mins = []
            
            #for each selected cluster...
            for key in checked_clusts:
                #it if has spikes...
                if len(self.gui.wave_dict[str(channel)][str(key)]) > 0:
                    
                    #list for keeping track of SEM values
                    sem_collec = []
                    sem_x_vals = []
                    
                    #add the average waveform to the appropriate list, followed by None to break it up
                    wave_collec += self.gui.avg_wave_dict[str(channel)][str(key)].tolist()
                    wave_collec.append(None)
                    
                    #calculate the high and low SEM lines
                    high_sem = (self.gui.avg_wave_dict[str(channel)][str(key)] + self.gui.wave_sem_dict[str(channel)][str(key)]).tolist()
                    low_sem = (self.gui.avg_wave_dict[str(channel)][str(key)] - self.gui.wave_sem_dict[str(channel)][str(key)]).tolist()
                    
                    #add the high SEM line then the reverse of the low SEM line to the SEM line list
                    sem_collec += high_sem
                    sem_collec += low_sem[::-1]
                    
                    #grab the correct colors
                    for i in range(self.gui.num_samples):
                        colors.append(self.gui.canvas3d.color_ops[int(key)])
                        sem_colors.append(self.gui.canvas3d.color_ops[int(key)])
                        
                    #add an empty color for the None entry
                    colors.append([0,0,0,0])
                    
                    #add more SEM colors for the lower line
                    for i in range(self.gui.num_samples):
                        sem_colors.append(self.gui.canvas3d.color_ops[int(key)])
                    
                    #add the appropriate x-values
                    x_vals += range(-8,self.gui.num_samples-7)
                    sem_x_vals += range(-8,self.gui.num_samples-8)
                    sem_x_vals += range(-8,self.gui.num_samples-8)[::-1]
                    
                    #figure out our max and min values for setting bounds
                    sem_maxs.append(np.max(sem_collec))
                    sem_mins.append(np.min(sem_collec))
                    
                    #stack together the coordinates for the SEM polygon
                    sem_pos = np.swapaxes(np.vstack((sem_x_vals,sem_collec)),0,1)
                    
                    #add the polygon to the appropriate dict
                    if channel==0:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel1.scene)
                    if channel==1:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel2.scene)
                    if channel==2:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel3.scene)
                    if channel==3:
                        self.poly_dict[str(channel)][str(key)] = visuals.Polygon(pos=sem_pos,color=self.gui.canvas3d.color_ops[int(key)],border_color=[0,0,0,0],parent=self.channel4.scene)

            #stack together the coordinates for the avg waveforms
            pos = np.swapaxes(np.vstack((x_vals,wave_collec)),0,1)
            
            #if we have colors (why is this necessary?)                
            if len(colors) > 0:
                #make it an array, change alpha to 1 (highlighted)
                colors = np.asarray(colors)
                colors[:,3] = 1
            else:
                #otherwise add an empty color
                colors.append([0,0,0,0])
            
            #set the data for the waveforms and set appropriate camera bounds
            if channel==0:
                self.waveline1.set_data(pos,color=colors,width=2)
                self.channel1.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-1.1*np.min(sem_mins)
            elif channel==1:
                self.waveline2.set_data(pos,color=colors,width=2)
                self.channel2.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-1.1*np.min(sem_mins)
            elif channel==2:
                self.waveline3.set_data(pos,color=colors,width=2)
                self.channel3.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-1.1*np.min(sem_mins)
            elif channel==3:
                self.waveline4.set_data(pos,color=colors,width=2)
                self.channel4.camera.rect = -8,1.1*np.min(sem_mins),40,1.1*np.max(sem_maxs)-1.1*np.min(sem_mins)
        
    def on_dblclick(self, event):
        ''' handles plot zooming in response to double click '''
        
        #if left mouse button...
        if event.button == 1:
            #figure out which channel (viewbox) the click was in
            viewbox = self.canvas.visual_at(event.pos)
            
            #if it's a 4-channel plot already...
            if self.plot == 'all':
                #make the grid parentless to clear the plot
                self.grid.parent = None
                
                #remake the plot according to the channel that was clicked on
                if viewbox == self.channel1:
                    self.init_plots(1)
                elif viewbox == self.channel2:
                    self.init_plots(2)
                elif viewbox == self.channel3:
                    self.init_plots(3)
                elif viewbox == self.channel4:
                    self.init_plots(4)
                    
            else:
                #otherwise, clear the last plot and plot all channels
                self.last_plot.parent = None
                self.init_plots('all')
            