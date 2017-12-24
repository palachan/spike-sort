# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 11:48:39 2017

2d waveform sorting class

@author: Patrick
"""

#import necessary modules
import numpy as np
from vispy import scene
import vispy.color
import vispy.visuals
import vispy.util
from vispy.scene import visuals
import copy

#import cluster_edit functions
import cluster_edit

#import GUI elements
from PySide import QtGui


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class WaveformScene(QtGui.QWidget):
    ''' class for plotting interactive 2D waveform cutting plot '''
    
    def __init__(self, gui, keys='interactive', plot='all'):
        #init the widget
        super(WaveformScene, self).__init__()
        #reference to the main gui instance
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(200,200)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        box.addWidget(self.canvas.native)
        
        #connect mouse events to appropriate functions
        self.canvas.events.mouse_double_click.connect(self.on_dblclick)
        self.canvas.events.mouse_press.connect(self.on_mouse_click)

        #call a function to initialize the plots (all 4)        
        self.init_plots(plot)
        
    def init_plots(self,plot):
        ''' creates the plotting scene '''
        
        #grab the plot we're trying to make (either all for subplot view or 
        #one of the four for zoom view)
        self.plot = plot
        
        #if we're plotting all hte channels...
        if plot == 'all':
            #add a grid to plot things on
            self.grid = self.canvas.central_widget.add_grid()
        
            #add a view to the grid for each channel
            self.channel1 = self.grid.add_view(row=0, col=0)
            self.channel2 = self.grid.add_view(row=0, col=1)
            self.channel3 = self.grid.add_view(row=1, col=0)
            self.channel4 = self.grid.add_view(row=1, col=1)

            #add gridlines to each view
            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
    
            #create a panzoom camera for each view
            self.channel1.camera = 'panzoom'
            self.channel2.camera = 'panzoom'
            self.channel3.camera = 'panzoom'
            self.channel4.camera = 'panzoom'
            
            #initialize a line visual for plotting the waveforms
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            self.waveline4 = visuals.Line(parent=self.channel4.scene)
            
            #initialize a Markers visual for plotting the selection markers
            self.thresh_points1 = visuals.Markers(parent=self.channel1.scene)
            self.thresh_points2 = visuals.Markers(parent=self.channel2.scene)
            self.thresh_points3 = visuals.Markers(parent=self.channel3.scene)
            self.thresh_points4 = visuals.Markers(parent=self.channel4.scene)
            
        #if we're plotting channel 1, just plot that
        elif plot == 1:
            self.channel1 = self.canvas.central_widget.add_view()

            grid1 = visuals.GridLines(scale=(.1,.1),parent=self.channel1.scene)
            self.channel1.camera = 'panzoom'
            self.waveline1 = visuals.Line(parent=self.channel1.scene)
            self.thresh_points1 = visuals.Markers(parent=self.channel1.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel1
            
        #if we're plotting channel 2, just plot that
        elif plot == 2:
            self.channel2 = self.canvas.central_widget.add_view()

            grid2 = visuals.GridLines(scale=(.1,.1),parent=self.channel2.scene)
            self.channel2.camera = 'panzoom'
            self.waveline2 = visuals.Line(parent=self.channel2.scene)
            self.thresh_points2 = visuals.Markers(parent=self.channel2.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel2
            
        #if we're plotting channel 3...
        elif plot == 3:
            self.channel3 = self.canvas.central_widget.add_view()

            grid3 = visuals.GridLines(scale=(.1,.1),parent=self.channel3.scene)
            self.channel3.camera = 'panzoom'
            self.waveline3 = visuals.Line(parent=self.channel3.scene)
            self.thresh_points3 = visuals.Markers(parent=self.channel3.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel3
            
        #if we're plotting channel 4...
        elif plot == 4:
            self.channel4 = self.canvas.central_widget.add_view()

            grid4 = visuals.GridLines(scale=(.1,.1),parent=self.channel4.scene)
            self.channel4.camera = 'panzoom'
            self.waveline4 = visuals.Line(parent=self.channel4.scene)
            self.thresh_points4 = visuals.Markers(parent=self.channel4.scene)
            
            #note which channel we're plotting
            self.last_plot = self.channel4
            
        #make lists to hold wave selection points (thresholds) for each channel
        self.thresh_points = [[],[],[],[]]
        #dummy variables, will keep track of which sample numbers have been
        #clicked on for each channel
        self.last_sample = [-100,-100,-100,-100]
        
        #add data to the plots!
        self.update_plots()
        
    def update_plots(self):
        ''' update the waveform plots with the latest data '''
        
        #create a list of the channels that are being plotted
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
        
        #create a list for the clusters we're plotting
        checked_clusts = []
        
        #assign unclassified waveforms to the appropriate waveform dict entry
        for channel in range(self.gui.num_channels):
            self.gui.wave_dict[str(channel)][str(0)] = self.gui.waveforms[channel][np.asarray(self.gui.cluster_dict[str(0)],dtype=np.int)]
        
        #if some cluster buttons are pressed...
        if len(self.gui.checked_clusts) > 0:
            #for each channel...
            for channel in range(self.gui.num_channels):
                #for each selected cluster, if it has spikes...
                for key in self.gui.checked_clusts:
                    if len(self.gui.cluster_dict[str(key)]) > 0:
                        #add it to checked_clusts
                        checked_clusts.append(key)
                        #update the waveforms for that cluster
                        self.gui.wave_dict[str(channel)][str(key)] = self.gui.waveforms[channel][np.asarray(self.gui.cluster_dict[str(key)],dtype=np.int)]

        #if there aren't any selected clusters, we'll just plot unclassified spikes
        if len(checked_clusts) == 0:
            checked_clusts = [0]

        #for each channel...
        for channel in channel_list:
            #make lists for waveform colors, and point coordinates
            colors = []
            wave_collec = []
            x_vals = []
            #for each selected cluster...
            for key in checked_clusts:
                #set the max number of waveforms to 1000
                max_spikes = 1000.
                #figure out our step size to appropriately downsample the spikes
                step = int(np.ceil(float(len(self.gui.wave_dict[str(channel)][str(key)]))/max_spikes))
                #if there are spikes in the cluster...
                if len(self.gui.wave_dict[str(channel)][str(key)]) > 0:
                    #for each subsampled spike...
                    for wave in self.gui.wave_dict[str(channel)][str(key)][::step]:
                        #add the waveform voltage values to the wave list
                        wave_collec += wave.tolist()
                        #grab the appropriate color for the cluster
                        color = copy.deepcopy(self.gui.canvas3d.color_ops[int(key)])
                        #if we're plotting a real cluster, set alpha to .8 (highlighted)
                        if int(key) != 0:
                            color[3] = .8
                        #add the color to the color list as many times as there are points in the waveform
                        for i in range(self.gui.num_samples):
                            colors.append(color)
                        #add a None to the list to break up the line, along with an empty color
                        wave_collec.append(None)
                        colors.append([0,0,0,0])
                        
                    #add to our list of arbitrary x-values (0-40 repeating)
                    x_vals_now = np.tile(range(-8,self.gui.num_samples-7),len(self.gui.wave_dict[str(channel)][str(key)][::step])).tolist()
                    x_vals += x_vals_now
            
            #make the colors an array
            colors = np.asarray(colors)
            #stick the x and y vals together to make useable coordinates
            pos = np.swapaxes(np.vstack((x_vals,wave_collec)),0,1)

            #set the data for the appropriate channel and set the camera bounds
            #according to the data
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
        ''' zooms or unzooms the plot in response to a double click '''
        
        #if its the left mouse button...
        if event.button == 1:
            #figure out which viewbox was clicked in (i.e. which channel)
            viewbox = self.canvas.visual_at(event.pos)
            
            #if we already have a 4-channel plot...
            if self.plot == 'all':
                
                #remove the grid's parent so it disappears
                self.grid.parent = None
            
                #initialize a new plot according to the viewbox that was clicked
                if viewbox == self.channel1:
                    self.init_plots(1)
                elif viewbox == self.channel2:
                    self.init_plots(2)
                elif viewbox == self.channel3:
                    self.init_plots(3)
                elif viewbox == self.channel4:
                    self.init_plots(4)
                    
            else:
                #otherwise, remove the parent from the last single channel plot and
                #plot all the channels
                self.last_plot.parent = None
                self.init_plots('all')
                
    def on_mouse_click(self, event):
        ''' handles waveform cutting events '''
        
        #if LMB and CTRL are both pressed...
        if event.button == 1 and vispy.util.keys.CONTROL in event.modifiers:
            
            #figure out which viewbox the click was in (i.e. which channel)
            viewbox = self.canvas.visual_at(event.pos)
            
            #if all channels are plotted, figure out which channel the
            #viewbox corresponds to
            if self.plot == 'all':
                if viewbox == self.channel1:
                    channel = 0
                elif viewbox == self.channel2:
                    channel = 1
                elif viewbox == self.channel3:
                    channel = 2
                elif viewbox == self.channel4:
                    channel = 3
                    
            #otherwise, we already know the channel
            else:
                channel = self.plot - 1
                
            #grab the appropriate Markers visual for plotting selection markers
            #(named for their pseudo-status as threshold markers)
            if channel == 0:
                thresh_collec = self.thresh_points1
            elif channel == 1:
                thresh_collec = self.thresh_points2
            elif channel == 2:
                thresh_collec = self.thresh_points3
            elif channel == 3:
                thresh_collec = self.thresh_points4
                
            #if we're dealing with an all-channel plot...
            if self.plot == 'all':
                #perform a double transform (viewbox then scene) on the screen coordinates
                #to get plot coordinates
                x_val,y_val = viewbox.scene.transform.imap(viewbox.transform.imap(event.pos))[0:2]

            else:
                #otherwise, just do a single scene transform
                x_val,y_val = viewbox.scene.transform.imap(event.pos)[0:2]

            #find the sample number (x-value) we're dealing with
            sample = np.around(x_val)

            #if we haven't selected a point yet or if this is a new sample number...
            if len(self.thresh_points[channel]) == 0 or (len(self.thresh_points[channel])>0 and sample != self.last_sample[channel]):
                #plot the clicked position on the graph
                thresh_collec.set_data(pos=np.asarray([[sample,y_val]]),face_color='red')
                
                #add the y (thresh point) and x (sample) values to their respective lists
                self.thresh_points[channel]=[y_val]
                self.last_sample[channel] = sample
                
            #if we've already picked a point and the new point is at the same sample number...
            elif len(self.thresh_points[channel])==1 and sample == self.last_sample[channel] and len(self.gui.checked_clusts) == 1:
                #grab the y-value
                self.thresh_points[channel].append(y_val)
                #plot the clicked position in addition to the previously clicked position
                thresh_collec.set_data(pos=np.asarray([[sample,y_val],[sample,self.thresh_points[channel][0]]]),face_color='red')
                
                #figure out which thresh point is high and which is low
                high = np.max(self.thresh_points[channel])
                low = np.min(self.thresh_points[channel])
                
                #grab the cluster we're dealing with
                current_clust = int(self.gui.checked_clusts[0])
                                    
                #find the indices of the cluster waveforms that fall below the high marker
                high_inds = np.where(np.swapaxes(self.gui.waveforms,1,2)[channel][int(sample+8)] > low)[0]
                #find the indices that fall above the low marker
                low_inds = np.where(np.swapaxes(self.gui.waveforms,1,2)[channel][int(sample+8)] < high)[0]
                #grab the indices of the cluster spikes
                clust_inds = self.gui.cluster_dict[str(current_clust)]
                
                #find the waveforms that fall between the high and low markers
                mid_inds = np.intersect1d(high_inds,low_inds)
                #find the intersection of those waveforms and this cluster
                new_inds = np.intersect1d(mid_inds,clust_inds)
                                
                #add the new indices to the cluster dict
                self.gui.cluster_dict[str(current_clust)] = new_inds
                                
                #set the IDs for all the old spikes to 0, then fill in the new spikes
                self.gui.clusts[clust_inds] = 0
                self.gui.clusts[new_inds] = current_clust
                #update the waveform dict
                for i in range(len(self.gui.waveforms)):
                    self.gui.wave_dict[str(i)][str(current_clust)] = self.gui.waveforms[i][new_inds]
                #refresh the thresh_points list
                self.thresh_points[channel] = []
                #calc the new cluster metrics
                self.gui.lratios[str(self.gui.checked_clusts[0])],self.gui.iso_dists[str(self.gui.checked_clusts[0])] = cluster_edit.calc_l_ratio(self.gui.all_points,self.gui.cluster_dict[str(self.gui.checked_clusts[0])])
    
                #call the cluster_edit change_cluster function
                cluster_edit.change_cluster(self.gui)
