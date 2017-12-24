# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 10:28:22 2017

time view, isi hist, autocorr

@author: Patrick
"""

#import necessary modules
import numpy as np
from vispy import scene
from vispy.scene import visuals
import copy
from PySide import QtGui


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class ISIScene(QtGui.QWidget):
    ''' class for plotting ISI histograms and spike time plot '''
    
    def __init__(self, gui, keys='interactive'):
        #initialize
        super(ISIScene, self).__init__()
        #reference to main GUI instance
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(200,200)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        box.addWidget(self.canvas.native)
        
        #create a view for the plot
        self.view = self.canvas.central_widget.add_view()
        #add a PanZoom camera
        self.view.camera = 'panzoom'
        
        #add a grid to the view
        self.grid = visuals.GridLines(scale=(.1,.1),parent=self.view.scene)
        #add a vertical line at 1ms to denote ISIs that are too short
        self.vline = visuals.InfiniteLine(pos=1000,color=[1,0,0,1],vertical=True,parent=self.view.scene)
        
        #start a dictionary for holding histograms
        self.hist_dict = {}
        
        #calculate our ISIs and timestamps
        self.refresh_times()

    def refresh_times(self):
        ''' calculates ISIs and timestamps for each cluster '''
            
        #for each cluster...
        for key in self.gui.cluster_dict.keys():
            #if there are spikes in the cluster...
            if len(self.gui.cluster_dict[key]) > 0:
                #grab the appropriate timestamps, in ascending order
                spike_timestamps = np.sort(self.gui.timestamps[self.gui.cluster_dict[key]])
                #make an entry for the ISI dict
                self.gui.isi_dict[key] = []
                #for each spike...
                for i in range(len(spike_timestamps)-1):
                    #calculate the ISI and scale to microseconds according to sample rate
                    isi = spike_timestamps[i+1]-spike_timestamps[i]
                    isi *= 1000000./self.gui.samplerate
                    #collect ISIs under 300 milliseconds
                    if isi<300000:
                        self.gui.isi_dict[key].append(isi)

                #add timestamps to the appropriate entry in timestamp dict
                self.gui.timestamp_dict[key] = spike_timestamps
                    
            #otherwise make empty entries
            else:
                self.gui.timestamp_dict[key] = []
                self.gui.isi_dict[key] = []  
            
            
    def update_plots(self):
        ''' update the data in the histogram view '''
        
        #if there are no clusters selected, we'll just show unclassified spikes
        if len(self.gui.checked_clusts) == 0:
            checked_clusts = [0]
        #otherwise we'll show the selected spikes
        else:
            checked_clusts = np.asarray(self.gui.checked_clusts,dtype=np.int)
            #assume that all the clusters are empty
            all_empty = True
            #check if each cluster is empty - if not, make note of it
            for clust in checked_clusts:
                if len(self.gui.cluster_dict[str(clust)]) > 0:
                    all_empty = False
            #if all clusters are empty, we'll just show unclassified spikes
            if all_empty:
                checked_clusts = [0]

        #remove the parent from each existing histogram to clear the plot
        for key in self.hist_dict.keys():
            self.hist_dict[key].parent = None

        #start a list for setting view boundaries
        max_vals = []
        #for each selected cluster...
        for clust in checked_clusts:
            clust = int(clust)
            #if the cluster has spikes...
            if len(self.gui.isi_dict[str(clust)]) > 0:
                #grab the appropriate color
                color = copy.deepcopy(self.gui.canvas3d.color_ops[clust])
                #if a real cluster, set alpha to 1 (highlighted)
                if clust != 0:
                    color[3] = 1
                    
                #create an ISI histogram for the cluster, add to hist_dict
                self.hist_dict[str(clust)] = visuals.Histogram(data=self.gui.isi_dict[str(clust)],bins=50,color=color,parent=self.view.scene)
                
                #calculate the max y-val in the histogram and add to list
                max_vals.append(np.max(self.hist_dict[str(clust)].mesh_data.get_vertices()[:,1]))

        #if there are values in max_val list...
        if len(max_vals) > 0:
            #set bounds according to maximum max_val
            self.view.camera.rect = -10000,0,310000,1.1*np.max(max_vals)
                
    def plot_time(self):
        ''' create a popup spike time plot '''
        
        #create a canvas for plotting
        self.timecanvas = scene.SceneCanvas(keys='interactive',show=True)
        #add a view
        view = self.timecanvas.central_widget.add_view()
        
        #grab spike y-values from the first parameter of the 3D plotting data, stack
        #with timestamp values for each spike as the x-vals
        pos = np.swapaxes(np.vstack([self.gui.timestamps,self.gui.canvas3d.pos[:,1].flatten()]),0,1)
        
        #create a scatter plot, add the spike data
        scatter = visuals.Markers()
        scatter.set_data(pos=pos,edge_color=None, face_color=self.gui.canvas3d.colors, size=4)
        #add the plot to the view
        view.add(scatter)
        #add a PanZoom camera
        view.camera = 'panzoom'
        #set the camera bounds
        view.camera.rect = np.min(self.gui.timestamps),np.min(self.gui.canvas3d.pos[:,1].flatten()),np.max(self.gui.timestamps)-np.min(self.gui.timestamps),np.max(self.gui.canvas3d.pos[:,1].flatten())-np.min(self.gui.canvas3d.pos[:,1].flatten())
