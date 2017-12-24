# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 15:23:37 2017

3d spike sorting class

some elements pulled from https://github.com/vispy/vispy/issues/1028
and https://gist.github.com/jlaura/cb4d7af59e5e9a2824a4

@author: Patrick
"""

#import necessary modules
import numpy as np
from vispy import scene
import vispy.color
import vispy.visuals
import vispy.util
from vispy.scene import visuals
from matplotlib import path
from matplotlib import colors as mcolors

#import functions from cluster_editing script
import cluster_edit

#import GUI elements
from PySide import QtGui


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class ScatterScene(QtGui.QWidget):
    ''' class for plotting interactive 3D cluster-cutting scene '''
        
    def __init__(self, gui, keys='interactive'):
        
        #initialize the widget
        super(ScatterScene, self).__init__()
        
        #grab reference to main gui instance
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(500,500)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True)
        box.addWidget(self.canvas.native)

        #create a view for the canvas
        self.view = self.canvas.central_widget.add_view()
        
        #transform the cluster colors into RGBA values
        self.color_ops = mcolors.to_rgba_array(self.gui.cs,alpha=0.5)
        #make a list of colors for each spike based on list of cluster IDs
        self.colors = self.color_ops[self.gui.clusts]
        
        #get positions for spikes in the scatter plot
        self.pos = self.get_spike_positions(0,1,2,init=True)
                
        # create scatter (Markers) visual and fill in the data
        self.scatter = visuals.Markers()
        self.scatter.set_data(self.pos, edge_color=None, face_color=self.colors, size=4)
        #create a Polygon visual for implementing lasso selection
        self.lasso = visuals.Polygon(color=[0,0,0,0],border_color='white',border_width=4)
        #initialize the lasso trail but make it empty
        self.trail = []
        
        #add the visuals to the view
        self.view.add(self.lasso)
        self.view.add(self.scatter)
        #add a 3D axis for reference #TODO: can this be extended?
        self.axis = visuals.XYZAxis(parent=self.view.scene)
        #set a camera for the view
        self.view.camera = 'arcball'
        
        #create a method for transforming between screen and plot coordinates
        self.tr = self.view.scene.transform

        #add param labels according to the current parameters
        self.gui.param1label.setText('X - '+self.gui.params[0])
        self.gui.param2label.setText('Y - '+self.gui.params[1])
        self.gui.param3label.setText('Z - '+self.gui.params[2])
        
        #connect mouse events to appropriate functions
        self.canvas.events.mouse_move.connect(self.on_mouse_move)
        self.canvas.events.mouse_release.connect(self.on_mouse_release)
        
    def get_spike_positions(self,param1count,param2count,param3count,init=False):
        ''' get scatter positions for each spike in current feature space '''
        
        #set param counts according to arguments
        self.gui.param1count = param1count
        self.gui.param2count = param2count
        self.gui.param3count = param3count
        
        #get associated parameters (string 'Parameter Electrode')
        param1 = self.gui.params[param1count]
        param2 = self.gui.params[param2count]
        param3 = self.gui.params[param3count]
        
        #set the param labels accordingly
        self.gui.param1label.setText('X - '+param1)
        self.gui.param2label.setText('Y - '+param2)
        self.gui.param3label.setText('Z - '+param3)
        
        #grab the channel associated with each string
        param1_channel = int(param1[len(param1)-1])
        param2_channel = int(param2[len(param2)-1])
        param3_channel = int(param3[len(param3)-1])
        #list them
        channels = [param1_channel,param2_channel,param3_channel]
        
        #grab the parameter associated with each string
        p1 = param1[:len(param1)-2]
        p2 = param2[:len(param2)-2]
        p3 = param3[:len(param3)-2]
        #list them
        params = [p1,p2,p3]
        
        #for each new parameter, grab the associated feature values
        for i in range(len(params)):
            if params[i] == 'Peaks':
                params[i] = self.gui.peaks
            elif params[i] == 'Valleys':
                params[i] = self.gui.valleys
            elif params[i] == 'Energy':
                params[i] = self.gui.energy
            elif params[i] == 'PC1':
                params[i] = self.gui.pc1
            elif params[i] == 'PC2':
                params[i] = self.gui.pc2
            elif params[i] == 'PC3':
                params[i] = self.gui.pc3
            elif params[i] == 'Real PC1':
                params[i] = self.gui.realpc1
        
        #make an array for holding position values
        pos = np.zeros_like(self.gui.peaks[0:3])
        
        #assign the appropriate values to the position array
        for i in range(len(params)):
            pos[i] = params[i][channels[i]-1]
        
        #swap axes for some reason... (easier to feed into scatter function?)
        pos = pos.swapaxes(0,1)
            
        #if we're initializing stuff, just retern the positions
        if init:
            return pos
            
        #otherwise, set the new data for the plot
        self.scatter.set_data(pos, edge_color=None,face_color=self.colors,size=4)
        #make the data global
        self.pos = pos

    def on_mouse_move(self, event):
        ''' keep track of mouse dragging positions for lasso selection '''

        #if LMB and CTRL are down and mouse is dragging...
        if event.button == 1 and vispy.util.keys.CONTROL in event.modifiers and event.is_dragging:
            #grab the trail (in screen coordinates)
            self.screentrail=event.trail()
            #transform into real coordinates
            self.trail = self.tr.imap(self.screentrail)
            #just take the first three elements (x,y,z coordinates)
            self.trail = self.trail[:,[0,1,2]]
            #if the trail can make a polygon...
            if len(self.trail) > 3:
                #start drawing the lasso polygon!
                self.lasso.pos = self.trail
                #if we only have one selected cluster...
                if len(self.gui.checked_clusts) == 1:
                    #set the color of the polygon border to the cluster's color
                    self.lasso.border_color = self.gui.cs[int(self.gui.checked_clusts[0])]
                else:
                    #otherwise, make it gray (it won't do anything)
                    self.lasso.border_color = 'gray'
                            
    def on_mouse_release(self, event):
        ''' update cluster info once lasso selection has taken place '''
                
        #if the mouse trail can make a polygon...
        if len(self.trail) > 3:
            #get the screen positions of the lasso points
            self.screenpos = self.tr.map(self.pos)[:,[0,1]]
            #make it into a matplotlib Path collection
            p = path.Path(self.screentrail)
            #find the points that are inside the polygon (using screen coordinates,
            #returns a boolean array)
            inside = p.contains_points(self.screenpos)
            #change the boolean array into indices
            inside_inds = [index for index,value in enumerate(inside) if value]
            
            #if there's only one selected cluster...
            if len(self.gui.checked_clusts) == 1:
                #if there are already spikes in the cluster...
                if len(self.gui.cluster_dict[str(self.gui.checked_clusts[0])]) > 0:
                    #figure out the overlap between the existing spikes in the cluster 
                    #and the ones we just circled with the lasso, and remove 
                    #all other existing spikes in the cluster
                    self.gui.clusts[np.setdiff1d(self.gui.cluster_dict[str(self.gui.checked_clusts[0])],inside_inds)] = 0
                    self.colors[np.setdiff1d(self.gui.cluster_dict[str(self.gui.checked_clusts[0])],inside_inds)] = self.color_ops[0]
                    self.gui.cluster_dict[str(self.gui.checked_clusts[0])] = np.intersect1d(self.gui.cluster_dict[str(self.gui.checked_clusts[0])],inside_inds)
                    
                    #update every other cluster as well (in case we stole some spikes)
                    for key in self.gui.cluster_dict:
                        self.gui.cluster_dict[key] = [index for index,value in enumerate(self.gui.clusts.tolist()) if value == int(key)]
                        for channel in range(len(self.gui.waveforms)):
                            self.gui.wave_dict[str(channel)][str(key)] = self.gui.waveforms[channel][self.gui.cluster_dict[str(key)]]
                        self.gui.lratios[key],self.gui.iso_dists[key] = cluster_edit.calc_l_ratio(self.gui.all_points,self.gui.cluster_dict[key])
                        
                else:
                    #otherwise, just assign the circled spikes to the selected cluster
                    self.gui.clusts[inside] = int(self.gui.checked_clusts[0])
                    self.gui.cluster_dict[str(self.gui.checked_clusts[0])] = [index for index,value in enumerate(inside) if value]
                    self.colors[inside] = self.color_ops[int(self.gui.checked_clusts[0])]
                    
                    #update every other cluster in case we stole some spikes
                    for key in self.gui.cluster_dict:
                        self.gui.cluster_dict[key] = [index for index,value in enumerate(self.gui.clusts) if value == int(key)]
                        for channel in range(len(self.gui.waveforms)):
                            self.gui.wave_dict[str(channel)][str(key)] = self.gui.waveforms[channel][self.gui.cluster_dict[str(key)]]

                        self.gui.lratios[key],self.gui.iso_dists[key] = cluster_edit.calc_l_ratio(self.gui.all_points,self.gui.cluster_dict[key])
            
                #call cluster_edit change_cluster function
                cluster_edit.change_cluster(self.gui)
                       
            #make the lasso really small so we can't see it                             
            self.trail = [[0,0,0],[.0000000001,.0000000001,.0000000001]]
            self.lasso.pos = self.trail
            
    def update_colors(self):
        ''' update the colors in the 3D scatterplot '''
        
        #assign colors to each spike according to cluster ID
        self.colors = self.color_ops[self.gui.clusts]
        #change alpha to 1 for selected spikes (highlight them)
        for clust in self.gui.checked_clusts:
            self.colors[np.where(self.gui.clusts==int(clust)),np.array([3])] = 1
        #set the data/colors for the scatter plot
        self.scatter.set_data(pos=self.pos,edge_color=None, face_color=self.colors, size=4)
        