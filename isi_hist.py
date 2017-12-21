# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 10:28:22 2017

@author: Patrick
"""
import numpy as np

def refresh_times(self):
        
    for key in self.clust_dict.keys():
        if len(self.clust_dict[key]) > 0:
            spike_timestamps = self.timestamps[self.clust_dict[key]]
            self.isi_dict[key] = []
            for i in range(len(spike_timestamps)-1):
                self.isi_dict[key].append(spike_timestamps[i+1]-spike_timestamps[i])
            self.timestamp_dict[key] = spike_timestamps
        else:
            self.timestamp_dict[key] = []
            self.isi_dict[key] = []
            
def 


    #grab appropriate spike data
    isi_list = spike_data['isi_list']
    spike_train = spike_data['spike_train']
    
    #convert ISI times from microseconds to seconds
    for i in range(len(isi_list)):
        isi_list[i] = float(isi_list[i])/1000000.
    #remove ISIs longer than 1 second from the list    
    def remove_values_from_list(the_list, val):
        return [value for value in the_list if value < val]
    isi_list = remove_values_from_list(isi_list, 1)
    
    #make a histogram of the isi's
    isi_hist = np.histogram(isi_list,bins=1000,range=[0,1])
    
    isi_xvals = np.arange(0,1,1./1000.)
        
    #add the ISI hist to cluster data dict
    cluster_data['isi_hist'] = isi_hist
    cluster_data['isi_xvals'] = isi_xvals
    
    #note that ISI data is ready
    gui.metadata[trial_data['current_trial']][trial_data['current_cluster']][trial_data['current_cam_ind']]['dataready']['plot_isi'] = True
    #send updated data to the gui
    gui.worker.plotting_data.emit(ops,adv,trial_data,cluster_data,spike_data)