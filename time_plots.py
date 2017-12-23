# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 10:28:22 2017

time view, isi hist, autocorr

@author: Patrick
"""
import os
os.environ['QT_API'] = 'pyside'
import numpy as np
from vispy import scene
from vispy.scene import visuals
import copy
from PySide import QtGui


class ISIScene(QtGui.QWidget):
    
    def __init__(self, gui, keys='interactive', plot='all'):
        
        super(ISIScene, self).__init__()
        
        self.gui = gui
        self.plot = plot
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(200,200)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        
#        self.canvas.create_native()
        box.addWidget(self.canvas.native)
        
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'panzoom'
        
        grid = visuals.GridLines(scale=(.1,.1),parent=self.view.scene)
        vline = visuals.InfiniteLine(pos=1000,color=[1,0,0,1],vertical=True,parent=self.view.scene)
        
        self.hist_dict = {}
        
        self.refresh_times()

    def refresh_times(self):
            
        for key in self.gui.cluster_dict.keys():
            if len(self.gui.cluster_dict[key]) > 0:
                spike_timestamps = self.gui.timestamps[self.gui.cluster_dict[key]]
                self.gui.isi_dict[key] = []
                for i in range(len(spike_timestamps)-1):
                    isi = spike_timestamps[i+1]-spike_timestamps[i]
                    isi *= 1000000./30000.
                    if isi<300000:
                        self.gui.isi_dict[key].append(isi)

                
                self.gui.timestamp_dict[key] = spike_timestamps
                    
            else:
                self.gui.timestamp_dict[key] = []
                self.gui.isi_dict[key] = []
#                
#            try:
#                self.hist_dict[key]
#            except:
#                self.hist_dict[key] = visuals.Histogram(data=self.gui.isi_dict[key],bins=50)
                
            
            
    def update_plots(self):
        
        if len(self.gui.checked_clusts) == 0:
            checked_clusts = [0]
        else:
            checked_clusts = np.asarray(self.gui.checked_clusts,dtype=np.int)
            
        all_empty = True
        for clust in checked_clusts:
            if len(self.gui.cluster_dict[str(clust)]) > 0:
                all_empty = False
                
        if all_empty:
            checked_clusts = [0]

        for key in self.hist_dict.keys():
            self.hist_dict[key].parent = None

        max_vals = []
        for clust in checked_clusts:
            clust = int(clust)
            #make a histogram of the isi's
            if len(self.gui.isi_dict[str(clust)]) > 0:
                                
                color = copy.deepcopy(self.gui.canvas3d.color_ops[clust])
                if clust != 0:
                    color[3] = 1
                    

                self.hist_dict[str(clust)] = visuals.Histogram(data=self.gui.isi_dict[str(clust)],bins=50,color=color,parent=self.view.scene)
                
                max_vals.append(np.max(self.hist_dict[str(clust)].mesh_data.get_vertices()[:,1]))

        if len(max_vals) > 0:
            self.view.camera.rect = -10000,0,310000,1.1*np.max(max_vals)
                
    def plot_time(self):
        
        self.timecanvas = scene.SceneCanvas(keys='interactive',show=True)
        view = self.timecanvas.central_widget.add_view()
        
        pos = np.swapaxes(np.vstack([self.gui.timestamps,self.gui.canvas3d.pos[:,1].flatten()]),0,1)
        
        scatter = visuals.Markers()
        scatter.set_data(pos=pos,edge_color=None, face_color=self.gui.canvas3d.colors, size=4)
        
        view.add(scatter)
        
        view.camera = 'panzoom'
        view.camera.rect = np.min(self.gui.timestamps),np.min(self.gui.canvas3d.pos[:,1].flatten()),np.max(self.gui.timestamps)-np.min(self.gui.timestamps),np.max(self.gui.canvas3d.pos[:,1].flatten())-np.min(self.gui.canvas3d.pos[:,1].flatten())
