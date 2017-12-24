# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 11:09:38 2017

handles cluster stuff, like adding, deleting, merging, calculating metrics, etc.

@author: Patrick
"""
#import important stuff
import numpy as np
from scipy.stats import chi2

#import GUI elements
from PySide.QtGui import QPushButton,QKeySequence,QLabel


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def new_cluster(self,init=False):
    ''' create buttons, dictionary entries for new cluster --
    this can happen during file loading if a spike file already has 
    clusterIDs, in which case 'init' should be set to True '''
    
    #if we're not initializing things...
    if not init:
        #increment the cluster counter
        self.tot_clusts += 1
    #grab string copy of clust number 
    this_clust = str(self.tot_clusts)
    #create a new button, assign to clust_buttons dict
    self.clust_buttons[this_clust] = QPushButton(this_clust)
    #make it checkable, set a corresponding color
    self.clust_buttons[this_clust].setCheckable(True)
    self.clust_buttons[this_clust].setStyleSheet('QPushButton {background-color: %s}' % self.cs[self.tot_clusts])
    #set a shortcut for the button (cluster number key)
    self.clust_buttons[this_clust].setShortcut(QKeySequence(this_clust))
    #add to layout
    self.clusters_layout.addWidget(self.clust_buttons[this_clust])
    
    #if we're not initializing things...
    if not init:
        #create a new empty entry in cluster_dict
        self.cluster_dict[this_clust] = []
        #for each channel...
        for channel in range(self.num_channels):
            #create new empty entries in waveform dicts
            self.wave_dict[str(channel)][this_clust] = []
            
    #add a cluster label, set to None
    self.clust_labels[this_clust] = None
    
    #uncheck every current cluster button
    for key in self.clust_buttons:
        self.clust_buttons[key].setChecked(False)
    #check the new cluster button
    self.clust_buttons[this_clust].setChecked(True)
    
    #if we're not initializing stuff...
    if not init:
        #connect the button to change_cluster function
        self.clust_buttons[this_clust].toggled.connect(lambda: change_cluster(self))
        #set lratio and iso_dist for this cluster equal to NaN
        self.lratios[this_clust],self.iso_dists[this_clust] = [np.nan,np.nan]
        #call the change_cluster function
        change_cluster(self)
    else:
        #otherwise, calculate the lratio and isolation distance for the cluster
        self.lratios[this_clust],self.iso_dists[this_clust] = calc_l_ratio(self.all_points,self.cluster_dict[this_clust])        
            
def delete_cluster(self):
    ''' delete a cluster (or many) '''
    
    #for every current cluster...
    for key in self.clust_buttons.keys():
        #check if button is pressed (i.e. cluster should be deleted)
        if self.clust_buttons[key].isChecked():
            #set corresponding cluster ID indices equal to 0 
            self.clusts[self.clusts == int(key)] = 0
            #delete corresponding entries in data dicts
            del self.clust_buttons[key]
            del self.cluster_dict[key]
            del self.isi_dict[key]
            del self.timestamp_dict[key]
            for channel in range(self.num_channels):
                del self.wave_dict[str(channel)][key]
            
    #call shift_clusters function                        
    shift_clusters(self)
            
def merge_clusters(self):
    ''' merge two or more clusters into a single cluster '''
    
    #grab which clusters are currently selected
    checked = []
    for key in self.clust_buttons:
        if self.clust_buttons[key].isChecked():
            checked.append(int(key))
    
    #new clust ind is the smallest selected cluster
    new_clust = str(min(checked))
    #make a list for holding new spike indices
    new_inds = []
    
    #for each selected cluster...
    for clust in checked:
        #make string for dict indexing
        key = str(clust)
        #add spike indices to list for new cluster
        new_inds += np.asarray(self.cluster_dict[key]).tolist()
        #if this isn't the new cluster we're making...
        if key != new_clust:
            #delete relevant dictionary entries for the cluster
            del self.clust_buttons[key]
            del self.cluster_dict[key]
            del self.isi_dict[key]
            del self.timestamp_dict[key]
            for channel in range(len(self.waveforms)):
                del self.wave_dict[str(channel)][key]
            
    #assign new indices/cluster IDs to relevant dicts
    self.cluster_dict[new_clust] = new_inds
    self.clusts[new_inds] = int(new_clust)
    
    #assign new waveforms to waveform dict
    for channel in range(self.num_channels):
        self.wave_dict[str(channel)][new_clust] = self.waveforms[channel][self.cluster_dict[new_clust]]

    #calc new lratio and iso_dist
    self.lratios[new_clust],self.iso_dists[new_clust] = calc_l_ratio(self.all_points,self.cluster_dict[new_clust])
        
    #call shift_clusters function
    shift_clusters(self)
    
def shift_clusters(self):
    ''' move clusters around as a result of deletion or merging '''
    
    #gather old cluster numbers
    old_keys = []
    for key in self.clust_buttons:
        old_keys.append(int(key))
        
    #sort them in ascending order
    sorted_keys = np.sort(old_keys)
            
    #create new dicts for new clusters
    new_buttons = {}
    new_dict = {}
    new_wave_dict = {}
    new_lratios = {}
    new_iso_dists = {}
    for channel in range(self.num_channels):
        new_wave_dict[str(channel)] = {}
   
    #reset clust counter
    self.tot_clusts = 0
    #for each old cluster...
    for key in sorted_keys:
        #increment the total clusts counter
        self.tot_clusts += 1
        #get a string version of it for dict indexing etc.
        this_clust = str(self.tot_clusts)
        #make an entry in the new dicts equal to old cluster_dict entries
        new_dict[this_clust] = self.cluster_dict[str(key)]
        for channel in range(len(self.wave_dict)):
            new_wave_dict[str(channel)][this_clust] = self.wave_dict[str(channel)][str(key)]
        new_lratios[this_clust] = self.lratios[str(key)]
        new_iso_dists[this_clust] = self.iso_dists[str(key)]
        #including new cluster buttons with new numbers
        new_buttons[this_clust] = self.clust_buttons[str(key)]
        new_buttons[this_clust].setText(this_clust)
        new_buttons[this_clust].setStyleSheet('QPushButton {background-color: %s}' % self.cs[self.tot_clusts])
        #set new cluster IDs in clusts array
        self.clusts[self.clusts == int(key)] = self.tot_clusts
        
    #make the new dicts official
    self.clust_buttons = new_buttons
    self.cluster_dict = new_dict
    self.wave_dict = new_wave_dict
    self.lratios = new_lratios
    self.iso_dists = new_iso_dists
    
    #remove all the old cluster buttons from the layout
    for i in reversed(range(self.clusters_layout.count())): 
        self.clusters_layout.itemAt(i).widget().setParent(None)
    #add back the cluster buttons label
    self.clusters_layout.addWidget(self.clusters_label)
    #add the new buttons to the layout, set shortcuts
    for key in range(1,self.tot_clusts+1):
        self.clusters_layout.addWidget(self.clust_buttons[str(key)])
        self.clust_buttons[str(key)].setShortcut(QKeySequence(str(key)))
            
    #call change_cluster function
    change_cluster(self)
    
def change_cluster(self):
    ''' change the current active cluster(s) '''
    
    #start a list for holding which clusters are active
    self.checked_clusts = []
    #for each cluster button...
    for key in self.clust_buttons:
        #if button is checked, add cluster to list
        if self.clust_buttons[key].isChecked():
            self.checked_clusts.append(key)

    #for each available cluster info label...
    for key in self.clust_labels:
        #if the label exists (i.e. is present) but the cluster is not active...
        if self.clust_labels[key] is not None and key not in self.checked_clusts:
            #erase the text
            self.clust_labels[key].setText('')
            #remove the label from the layout, set dict entry equal to None
            self.params_layout.removeWidget(self.clust_labels[key])
            self.clust_labels[key] = None
        #if the label exists and the cluster is active...
        elif self.clust_labels[key] is not None and key in self.checked_clusts:
            #set the cluster info label text
            self.clust_labels[key].setText('Cluster %s: %d spikes \n Lratio: %f \n Iso Dist: %f' % (key,len(self.cluster_dict[key]),self.lratios[key],self.iso_dists[key]))
        #if the label doesn't exist but the cluster is active...
        elif self.clust_labels[key] is None and key in self.checked_clusts:
            #make a new label and add it to the layout
            self.clust_labels[key] = QLabel('Cluster %s: %d spikes \n Lratio: %f \n Iso Dist: %f' % (key,len(self.cluster_dict[key]),self.lratios[key],self.iso_dists[key]))
            self.params_layout.addWidget(self.clust_labels[key])
            
    #call function to refresh plots
    refresh_plots(self)
    
def refresh_plots(self):
    ''' refresh the data for each plot '''
        
    #assign spikes for cluster zero (unclustered spikes)
    self.cluster_dict[str(0)] = [index for index,value in enumerate(self.clusts) if value==0]

    #update waveform plot
    self.canvaswaves.update_plots()
    #update 3D plot
    self.canvas3d.update_colors()
    #update avg waveform plot
    self.canvasavg.refresh_avg_waves()
    self.canvasavg.update_plots()
    #update ISI plot
    self.canvasisi.refresh_times()
    self.canvasisi.update_plots()
    
def calc_l_ratio(all_points,clust_inds):
    ''' calculate the lratio and isolation distance for a cluster '''

    #if the cluster has spikes (so we don't break the program)
    if len(clust_inds) > 0:
        #grab the feature values for the points within the cluster
        points = all_points[:,clust_inds]
        #find the means of the features
        mean_points = np.mean(np.swapaxes(points,0,1),axis=0)
        #find the covariance matrix of the features
        cov_matrix = np.cov(points)
            
        #use SVD to get inverse of covariance matrix in case it's too singular (which
        #will happen if we have shorted wires and the corresponding features are identical)
        u,s,v = np.linalg.svd(cov_matrix)
        invcov = np.dot(np.dot(v.T,np.linalg.inv(np.diagflat(s))),u.T)
    
        #get the feature values for all points outside the cluster ('noise spikes')
        other_points = np.swapaxes(np.delete(all_points,clust_inds,axis=1),0,1)
        #make an array for keeping track of every noise spike's distance from the center
        #of the cluster in 8-dimensional feature space (4 PC1, 4 energy)
        noise_dists = np.zeros(len(other_points),dtype=np.float)
            
        #for every noise spike...
        for i in range(len(other_points)):
            #get the difference between the spike's feature values and the mean
            #feature values of the cluster (i.e. the center of the cluster)
            diff = other_points[i] - mean_points
            #find the mahalanobis distance of the spike from the center
            mdist = np.dot(np.dot(diff.T,invcov),diff)
            #add the distance to the noise_dists aray
            noise_dists[i] = np.float(mdist)
    
        #lratio is equal to the summed chi-squared survival function (1 - cumulative density function)
        #of each spike's mahalanobis distance from the center of the cluster with 8 degees
        #of freedom, divided by the number of spikes in the cluster
        lratio = np.sum(chi2.sf(noise_dists,df=8))/len(clust_inds)
    
        #sort the noise_dists in ascending order
        noise_dists = np.sort(noise_dists)
        
        #if there are fewer noise spikes than cluster spikes (n), the isolation distance is
        #equal to the mahalanobis distance of nth closest noise spike
        if len(noise_dists) > len(clust_inds):
            iso_distance = noise_dists[len(clust_inds)-1]
        #otherwise it's undefined
        else:
            iso_distance = np.nan
            
    else:
        lratio = np.nan
        iso_distance = np.nan

    #return our metrics
    return lratio,iso_distance
