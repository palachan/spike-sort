# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 15:23:37 2017

3d spike sorting class

some elements pulled from https://github.com/vispy/vispy/issues/1028
and https://gist.github.com/jlaura/cb4d7af59e5e9a2824a4

@author: Patrick
"""


import os
os.environ['QT_API'] = 'pyside'
import numpy as np
from vispy import scene
import vispy.color
import vispy.visuals
import vispy.util
import time
from vispy.scene import visuals
from matplotlib import path
from matplotlib import colors as mcolors
import cluster_edit
from PySide import QtGui, QtCore

class ScatterScene(QtGui.QWidget):
    
    change_params = QtCore.Signal(str,str,str)
    
    def __init__(self, gui, keys='interactive'):
        
        super(ScatterScene, self).__init__()
        
        self.gui = gui
        
        #Layout and canvas creation
        box = QtGui.QVBoxLayout(self)
        self.resize(500,500)
        self.setLayout(box)
        self.canvas = scene.SceneCanvas(keys=keys,show=True,create_native=True)
        box.addWidget(self.canvas.native)
        
        self.canvas.events.mouse_move.connect(self.on_mouse_move)
        self.canvas.events.mouse_release.connect(self.on_mouse_release)

        self.trail = []

        self.view = self.canvas.central_widget.add_view()

        self.pos = self.gui.peaks[:,[0,1,2]]
        
        self.gui.param1label.setText('X - '+self.gui.params[0])
        self.gui.param2label.setText('Y - '+self.gui.params[1])
        self.gui.param3label.setText('Z - '+self.gui.params[2])
        
        self.color_ops = mcolors.to_rgba_array(self.gui.cs,alpha=0.5)
        self.colors = self.color_ops[self.gui.clusts]
        
        self.screenpos = self.view.scene.transform.map(self.pos)[:,[0,1]]
        
        # create scatter object and fill in the data
        self.scatter = visuals.Markers()
        self.scatter.set_data(self.pos, edge_color=None, face_color=self.colors, size=4)
        
        self.lasso = visuals.Polygon(color=[0,0,0,0],border_color='white',border_width=4)
        self.view.add(self.lasso)
        self.view.add(self.scatter)
        self.view.camera = 'arcball'
#        self.view.camera.distance = 100
        
        self.change_params.connect(self.get_spike_positions)
        
        self.tr = self.view.scene.transform
        
        axis = visuals.XYZAxis(parent=self.view.scene)
        
    def get_spike_positions(self,param1count,param2count,param3count):
        
        self.gui.param1count = param1count
        self.gui.param2count = param2count
        self.gui.param3count = param3count
        
        param1 = self.gui.params[param1count]
        param2 = self.gui.params[param2count]
        param3 = self.gui.params[param3count]
        
        self.gui.param1label.setText('X - '+self.gui.params[param1count])
        self.gui.param2label.setText('Y - '+self.gui.params[param2count])
        self.gui.param3label.setText('Z - '+self.gui.params[param3count])
        
        param1_channel = int(param1[len(param1)-1])
        param2_channel = int(param2[len(param2)-1])
        param3_channel = int(param3[len(param3)-1])
        
        channels = [param1_channel,param2_channel,param3_channel]
        
        p1 = param1[:len(param1)-2]
        p2 = param2[:len(param2)-2]
        p3 = param3[:len(param3)-2]
        
        params = [p1,p2,p3]
        
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
        
        pos = np.swapaxes(np.zeros_like(self.pos),0,1)
        
        for i in range(len(params)):
            pos[i] = params[i][:,channels[i]-1]
            
        pos = np.swapaxes(pos,0,1)
        self.scatter.set_data(pos, edge_color=None,face_color=self.colors,size=4)
            
        self.pos = pos

    def on_mouse_move(self, event):

        if event.button == 1 and vispy.util.keys.CONTROL in event.modifiers and event.is_dragging:
            self.screentrail=event.trail()
            self.trail = self.tr.imap(self.screentrail)
            self.trail = self.trail[:,[0,1,2]]
            if len(self.trail) > 3:
                self.lasso.pos = self.trail
                if len(self.gui.checked_clusts) == 1:
                    self.lasso.border_color = self.gui.cs[int(self.gui.checked_clusts[0])]
                else:
                    self.lasso.border_color = 'gray'
                            
    def on_mouse_release(self, event):
                
        if len(self.trail) > 3:
            
            self.screenpos = self.view.scene.transform.map(self.pos)[:,[0,1]]
            p = path.Path(self.screentrail)
            inside = p.contains_points(self.screenpos)
            inside_inds = [index for index,value in enumerate(inside) if value]
            
            if len(self.gui.checked_clusts) == 1:
                if len(self.gui.cluster_dict[str(self.gui.checked_clusts[0])]) > 0:
                    self.gui.clusts[np.setdiff1d(self.gui.cluster_dict[str(self.gui.checked_clusts[0])],inside_inds)] = 0
                    self.colors[np.setdiff1d(self.gui.cluster_dict[str(self.gui.checked_clusts[0])],inside_inds)] = self.color_ops[0]
                    self.gui.cluster_dict[str(self.gui.checked_clusts[0])] = np.intersect1d(self.gui.cluster_dict[str(self.gui.checked_clusts[0])],inside_inds)
                    
                    for key in self.gui.cluster_dict:
                        self.gui.cluster_dict[key] = [index for index,value in enumerate(self.gui.clusts.tolist()) if value == int(key)]
                        for channel in range(len(self.gui.waveforms)):
                            self.gui.wave_dict[str(channel)][str(key)] = self.gui.waveforms[channel][self.gui.cluster_dict[str(key)]]
                            self.gui.wavepoint_dict[str(channel)][str(key)] = self.gui.wavepoints[channel][:,self.gui.cluster_dict[str(key)]]
                    
                else:
                    self.gui.clusts[inside] = int(self.gui.checked_clusts[0])
                    self.gui.cluster_dict[str(self.gui.checked_clusts[0])] = [index for index,value in enumerate(inside) if value]
                    self.colors[inside] = self.color_ops[int(self.gui.checked_clusts[0])]
                    
                    for key in self.gui.cluster_dict:
                        self.gui.cluster_dict[key] = [index for index,value in enumerate(self.gui.clusts) if value == int(key)]
                        for channel in range(len(self.gui.waveforms)):
                            self.gui.wave_dict[str(channel)][str(key)] = self.gui.waveforms[channel][self.gui.cluster_dict[str(key)]]
                            self.gui.wavepoint_dict[str(channel)][str(key)] = self.gui.wavepoints[channel][:,self.gui.cluster_dict[str(key)]]

                self.gui.lratios[str(self.gui.checked_clusts[0])],self.gui.iso_dists[str(self.gui.checked_clusts[0])] = cluster_edit.calc_l_ratio(self.gui.all_points,self.gui.cluster_dict[str(self.gui.checked_clusts[0])])
            
                cluster_edit.change_cluster(self.gui)
                                                    
            self.trail = [[0,0,0],[.0000000001,.0000000001,.0000000001]]

            self.lasso.pos = self.trail
            
    def update_colors(self):
        
        self.colors = self.color_ops[self.gui.clusts]
        
        for clust in self.gui.checked_clusts:
            self.colors[np.where(self.gui.clusts==int(clust)),np.array([3])] = 1
        
        self.scatter.set_data(pos=self.pos,edge_color=None, face_color=self.colors, size=4)
        
        

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    view = ScatterScene(keys='interactive')
    view.show()
    app.exec_()