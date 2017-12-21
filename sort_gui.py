# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 12:37:38 2017

spike sort gui

@author: Patrick
"""

import os
os.environ['QT_API'] = 'pyside'
import matplotlib as mpl
mpl.rcParams['backend.qt4']='PySide'
mpl.use('Qt4Agg')
import sys
import pickle
import time
import numpy as np
from OpenEphys import loadSpikes
from collections import deque
#import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib import path
from matplotlib import colors as mplcolors
import copy
import cluster_edit
import files

from PySide.QtCore import (QProcess,QRect,Qt,QObject,Signal,Slot,QThread,QEventLoop,QTimer)
from PySide.QtGui import (QApplication, QMainWindow, QFrame, QLabel, QCheckBox, QLineEdit,
                          QAction, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,QTextCursor,
                          QTextEdit, QMenuBar, QMenu, QStatusBar, QStyle, QPushButton, QFileDialog, QDesktopWidget)

#import main
#import plot

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import sort_2d
import wave_cut
import avg_waves
import time_plots

#class for MainWindow instance
class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        ''' sets up the whole main window '''
        
        #standard init
        super(MainWindow, self).__init__(parent)
        #set the window size in pixels
#        self.resize(1100, 700)
        #set the window title
        self.setWindowTitle('spike_sort')
        
        self.screen_height = QDesktopWidget().screenGeometry().height()
        self.screen_width = QDesktopWidget().screenGeometry().width()
        
        
        #assign a layout to the main window
        self.mainlayout = QGridLayout()

        #make widgets
        self.setup_mpl_canvas()
        self.setup_side_canvases()
        self.setup_param_buttons()
        self.setup_random_buttons()
        self.setup_cluster_buttons()
        self.setup_fullscreen_buttons()

        #add the matplotlib NavigationToolbar above plotting canvas
        self.toolbar = NavigationToolbar(self.maincanvas, self)
        self.toolbar.setGeometry(QRect(self.screen_width*.1, self.screen_height*.03, self.screen_width*.25, self.screen_height*.07))
        self.mainlayout.addWidget(self.toolbar)
        
        #create a QMenuBar and set geometry
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, self.screen_width*.5, self.screen_height*.03))
        #set the QMenuBar as menu bar for main window
        self.setMenuBar(self.menubar)
        
        self.setup_file_menu()
        self.setup_view_menu()
        
        self.peaks_button.clicked.connect(lambda: sort_2d.plot_peaks(self))
        self.valleys_button.clicked.connect(lambda: sort_2d.plot_valleys(self))
        self.energy_button.clicked.connect(lambda: sort_2d.plot_energy(self))
        
        self.new_button.clicked.connect(lambda: cluster_edit.new_cluster(self))
        self.delete_button.clicked.connect(lambda: cluster_edit.delete_cluster(self))
        self.merge_button.clicked.connect(lambda: cluster_edit.merge_clusters(self))
        
        self.plot_figs = {}
        self.plot_figs['param_view'] = self.mainfigure
        self.plot_figs['wave_view'] = self.topfigure
        self.plot_figs['avg_wave'] = self.midfigure
        self.plot_figs['isi_hist'] = self.lowfigure
        
        self.plot_list = ['param_view','wave_view','avg_wave','isi_hist']
        self.canv_list = ['main','top','mid','low']
        self.cs=['grey','red','beige','green','skyblue','pink','limegreen','magenta','blue','purple','orange','yellow','fuchsia','greenyellow','mintcream','orchid']
        self.clust_colors = mplcolors.ListedColormap(self.cs)
        self.norm=mplcolors.Normalize(vmin=0,vmax=len(self.cs)-1)
        
        self.showMaximized()
        
    def open_file(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Open Spike File', '','Openephys spike files (*.spikes)')
        spike_data = loadSpikes(self.fname[0])
        
        sample_nums = spike_data['timestamps']
        self.framerate = spike_data['header']['sampleRate']
        #get timestamps in microseconds
        self.timestamps = sample_nums*1000000/self.framerate
        #norm so they start at 0
        self.timestamps = self.timestamps - np.min(self.timestamps)
        
        waveforms = np.swapaxes(spike_data['spikes'],1,2)
        self.peaks = sort_2d.find_peaks(waveforms)
        self.valleys = sort_2d.find_valleys(waveforms)
        self.energy = self.peaks**2
        
        self.num_spikes = len(waveforms)
        self.wavepoints = np.swapaxes(spike_data['spikes'],0,2)
        self.waveforms = np.swapaxes(waveforms,0,1)
        self.canvas_label.setText('2d parameters')
        self.canvas_label_top.setText('waveforms')
        self.canvas_label_mid.setText('average waveforms')
        self.canvas_label_low.setText('isi histogram')
        
        self.cluster_dict = {}
        self.clust_buttons = {}
        self.wave_dict = {}
        self.wavepoint_dict = {}
        self.avg_wave_dict = {}
        self.isi_dict = {}
        self.timestamp_dict = {}
        self.wave_sem_dict = {}
        
        for channel in range(len(self.waveforms)):
            self.wave_dict[str(channel)] = {}
            self.wavepoint_dict[str(channel)] = {}
            self.avg_wave_dict[str(channel)] = {}
            self.wave_sem_dict[str(channel)] = {}
        
        self.checked_clusts = []
        self.tot_clusts = 0
        self.clusts = np.zeros(self.num_spikes,dtype=np.int)
        self.thresh_points = [[],[],[],[]]
        self.last_sample = [0,0,0,0]
    
        self.waveplot = 'all'
        self.paramplot = 'all'
        self.avgplot = 'all'
        
        self.param = self.peaks
        
        sort_2d.draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)
        cluster_edit.refresh_plots(self)
        
        self.main_cid = self.plot_figs['param_view'].canvas.mpl_connect('button_press_event', lambda event: sort_2d.on_click(self,event))
        self.top_cid = self.plot_figs['wave_view'].canvas.mpl_connect('button_press_event', lambda event: wave_cut.on_press(self,event))
        self.mid_cid = self.plot_figs['avg_wave'].canvas.mpl_connect('button_press_event', lambda event: avg_waves.on_click(self,event))
        self.low_cid = None
        
    def save_ts(self):
        
        trodefile = os.path.basename(self.fname[0])
        save_dir = os.path.dirname(self.fname[0])
        
        for key in self.timestamp_dict.keys():
            if int(key) < 10:
                cname = '0' + key
            else:
                cname = key
            ts_file = open(save_dir + '/' + trodefile[:3]+'_SS_'+cname+'.txt', 'w')
            for ts in self.timestamp_dict[key]:
                ts_file.write("%s\n" % ts)
        
    def setup_file_menu(self):
        fileMenu = QMenu('&File',self)
        self.menubar.addMenu(fileMenu)
        
        fileMenu.addAction('&Open spike file',self.open_file, 'Ctrl+O')
#        fileMenu.addAction('&Save spike file', self.save_file, 'Ctrl+S')
        fileMenu.addAction('&Save timestamp file', self.save_ts, 'Ctrl+T')
        
    def setup_view_menu(self):
        viewMenu = QMenu('&View',self)
        self.menubar.addMenu(viewMenu)
        
        viewMenu.addAction('&Time plot', lambda: time_plots.plot_time(self), 'Ctrl+F4')

    def setup_random_buttons(self):
        #make QFrame
        rb = QFrame(self)
        #make and set label
#        rb_label = QLabel()
#        rb_label.setText('')
        #set gemoetry and color
        rb.setGeometry(QRect(self.screen_width*.23, self.screen_height*.83, self.screen_width*.34, self.screen_height*.07))
        rb.setObjectName("random_buttonsWidget")
        rb.setStyleSheet("#random_buttonsWidget {background-color:gray;}")
        #create and set layout
        rb_layout = QHBoxLayout()
        rb.setLayout(rb_layout)
        #make labview checkbox
        self.new_button = QPushButton('new cluster') 
        self.delete_button = QPushButton('delete cluster(s)')
        self.merge_button = QPushButton('merge clusters')
        #add to layout
        #rb_layout.addWidget(rb_label)        
        rb_layout.addWidget(self.new_button)
        rb_layout.addWidget(self.delete_button)
        rb_layout.addWidget(self.merge_button)
        
    def setup_cluster_buttons(self):
        #make QFrame
        clusters = QFrame(self)
        #make and set label
        self.clusters_label = QLabel()
        self.clusters_label.setText('clusters')
        #set gemoetry and color
        clusters.setGeometry(QRect(self.screen_width*.36, self.screen_height*.03, self.screen_width*.34, self.screen_height*.07))
        clusters.setObjectName("clustersWidget")
        clusters.setStyleSheet("#clustersWidget {background-color:gray;}")
        #create and set layout
        self.clusters_layout = QHBoxLayout()
        clusters.setLayout(self.clusters_layout)
        #add to layout
        self.clusters_layout.addWidget(self.clusters_label)        
#        clusters_layout.addWidget(clust_buttons['0'])
        self.clusters_layout.setAlignment(Qt.AlignLeft)
                
    def setup_param_buttons(self):
        #make QFrame
        params = QFrame(self)
        #make and set label
        params_label = QLabel()
        params_label.setText('parameters')
        #set gemoetry and color
        params.setGeometry(QRect(self.screen_width*.02, self.screen_height*.12, self.screen_width*.07, self.screen_height*.7))
        params.setObjectName("paramsWidget")
        params.setStyleSheet("#paramsWidget {background-color:gray;}")
        #create and set layout
        params_layout = QVBoxLayout()
        params_layout.setSpacing(15)
        params.setLayout(params_layout)
        #make labview checkbox
        self.peaks_button = QPushButton('peaks')
        self.valleys_button = QPushButton('valleys')
        self.energy_button = QPushButton('energy')

        #add to layout
        params_layout.addWidget(params_label)        
        params_layout.addWidget(self.peaks_button)
        params_layout.addWidget(self.valleys_button)
        params_layout.addWidget(self.energy_button)
        params_layout.setAlignment(Qt.AlignTop)
            
    def setup_fullscreen_buttons(self):
        fsb1 = QFrame(self)
        fsb1.setGeometry(QRect(self.screen_width*.9, self.screen_height*.085, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button1 = QPushButton('full')
        fsb1_layout = QHBoxLayout()
        fsb1_layout.addWidget(self.fullscreen_button1)
        fsb1.setLayout(fsb1_layout)
        
        fsb2 = QFrame(self)
        fsb2.setGeometry(QRect(self.screen_width*.9, self.screen_height*.355, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button2 = QPushButton('full')
        fsb2_layout = QHBoxLayout()
        fsb2_layout.addWidget(self.fullscreen_button2)
        fsb2.setLayout(fsb2_layout)
        
        fsb3 = QFrame(self)
        fsb3.setGeometry(QRect(self.screen_width*.9, self.screen_height*.635, self.screen_width*.055, self.screen_height*.06))
        self.fullscreen_button3 = QPushButton('full')
        fsb3_layout = QHBoxLayout()
        fsb3_layout.addWidget(self.fullscreen_button3)
        fsb3.setLayout(fsb3_layout)
        
        self.fullscreen_button1.clicked.connect(lambda: self.change_plots(1))
        self.fullscreen_button2.clicked.connect(lambda: self.change_plots(2))
        self.fullscreen_button3.clicked.connect(lambda: self.change_plots(3))
        
    def setup_mpl_canvas(self):
        ''' set up the matplotlib plotting canvas '''
        
        #create QFrame with parent self
        plot_frame = QFrame(self)
        #make a label for the canvas
        self.canvas_label = QLabel()
        #make label empty for now
        self.canvas_label.setText('')
        #set geometry
        plot_frame.setGeometry(QRect(self.screen_width*.1, self.screen_height*.12, self.screen_width*.6, self.screen_height*.7))
        #name the QFrame so we can give it a cool color
        plot_frame.setObjectName("main_canvas_widget")
        #give it a cool color
        plot_frame.setStyleSheet("#main_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        plot_layout = QVBoxLayout()
        plot_frame.setLayout(plot_layout)
        #create a matplotlib figure for plotting data to
        self.mainfigure = Figure()
        #create a canvas to show the figure on
        self.maincanvas = FigureCanvas(self.mainfigure)
        #add canvas and label to layout
        plot_layout.addWidget(self.canvas_label)
        plot_layout.addStretch(1)
        plot_layout.addWidget(self.maincanvas)
        plot_layout.addStretch(1)
    
    def setup_side_canvases(self):
        ''' set up bonus plotting canvases '''
        
        #create QFrame with parent self
        plot_frame_top = QFrame(self)
        #make a label for the canvas
        self.canvas_label_top = QLabel()
        #make label empty for now
        self.canvas_label_top.setText('')
        #set geometry
        plot_frame_top.setGeometry(QRect(self.screen_width*.72, self.screen_height*.1, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_top.setObjectName("top_canvas_widget")
        #give it a cool color
        plot_frame_top.setStyleSheet("#top_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        plot_layout_top = QVBoxLayout()
        plot_frame_top.setLayout(plot_layout_top)
        #create a matplotlib figure for plotting data to
        self.topfigure = Figure()
        #create a canvas to show the figure on
        self.topcanvas = FigureCanvas(self.topfigure)
        #add canvas and label to layout
        plot_layout_top.addWidget(self.canvas_label_top)
        plot_layout_top.addWidget(self.topcanvas)
        
        #create QFrame with parent self
        plot_frame_mid = QFrame(self)
        #make a label for the canvas
        self.canvas_label_mid = QLabel()
        #make label empty for now
        self.canvas_label_mid.setText('')
        #set geometry
        plot_frame_mid.setGeometry(QRect(self.screen_width*.72, self.screen_height*.37, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_mid.setObjectName("mid_canvas_widget")
        #give it a cool color
        plot_frame_mid.setStyleSheet("#mid_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        plot_layout_mid = QVBoxLayout()
        plot_frame_mid.setLayout(plot_layout_mid)
        #create a matplotlib figure for plotting data to
        self.midfigure = Figure()
        #create a canvas to show the figure on
        self.midcanvas = FigureCanvas(self.midfigure)
        #add canvas and label to layout
        plot_layout_mid.addWidget(self.canvas_label_mid)
        plot_layout_mid.addWidget(self.midcanvas)
        
        #create QFrame with parent self
        plot_frame_low = QFrame(self)
        #make a label for the canvas
        self.canvas_label_low = QLabel()
        #make label empty for now
        self.canvas_label_low.setText('')
        #set geometry
        plot_frame_low.setGeometry(QRect(self.screen_width*.72, self.screen_height*.65, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_low.setObjectName("low_canvas_widget")
        #give it a cool color
        plot_frame_low.setStyleSheet("#low_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        plot_layout_low = QVBoxLayout()
        plot_frame_low.setLayout(plot_layout_low)
        #create a matplotlib figure for plotting data to
        self.lowfigure = Figure()
        #create a canvas to show the figure on
        self.lowcanvas = FigureCanvas(self.lowfigure)
        #add canvas and label to layout
        plot_layout_low.addWidget(self.canvas_label_low)
        plot_layout_low.addWidget(self.lowcanvas)

    def change_plots(self,button):
        
        def rotate(lst, x):
            d = deque(lst)
            d.rotate(x)
            lst[:] = d
            return lst
            
        self.plot_list = rotate(self.plot_list,-button)
        self.plot_figs[self.plot_list[0]] = self.mainfigure
        self.plot_figs[self.plot_list[1]] = self.topfigure
        self.plot_figs[self.plot_list[2]] = self.midfigure
        self.plot_figs[self.plot_list[3]] = self.lowfigure

        self.mainfigure.clear()
        if self.main_cid is not None:
            self.mainfigure.canvas.mpl_disconnect(self.main_cid)
            
        self.topfigure.clear()
        if self.top_cid is not None:
            self.topfigure.canvas.mpl_disconnect(self.top_cid)

        self.midfigure.clear()
        if self.mid_cid is not None:
            self.midfigure.canvas.mpl_disconnect(self.mid_cid)

        self.lowfigure.clear()
        if self.low_cid is not None:
            self.lowfigure.canvas.mpl_disconnect(self.low_cid)
        
        wave_cut.plot_waveforms(self.waveforms,self)
        sort_2d.draw_plots(self.param,self.clusts,self.clust_colors,self.norm,self)
        
        avg_waves.refresh_avg_waves(self)
        avg_waves.plot_avg_waves(self)
        
        time_plots.refresh_times(self)
        time_plots.plot_isi(self)

        for plot in range(len(self.plot_list)):
            if self.plot_list[plot] == 'param_view':
                if plot == 0:
                    self.main_cid = self.mainfigure.canvas.mpl_connect('button_press_event', lambda event: sort_2d.on_click(self,event))
                    self.canvas_label.setText('2d parameters')
                    self.top_cid = self.topfigure.canvas.mpl_connect('button_press_event', lambda event: wave_cut.on_press(self,event))
                    self.canvas_label_top.setText('waveforms')
                    self.mid_cid = self.plot_figs['avg_wave'].canvas.mpl_connect('button_press_event', lambda event: avg_waves.on_click(self,event))
                    self.canvas_label_mid.setText('average waveforms')
                    self.low_cid = None
                    self.canvas_label_low.setText('isi histogram')
                elif plot == 1:
                    self.top_cid = self.topfigure.canvas.mpl_connect('button_press_event', lambda event: sort_2d.on_click(self,event))
                    self.canvas_label_top.setText('2d parameters')
                    self.mid_cid = self.midfigure.canvas.mpl_connect('button_press_event', lambda event: wave_cut.on_press(self,event))
                    self.canvas_label_mid.setText('waveforms')
                    self.low_cid = self.plot_figs['avg_wave'].canvas.mpl_connect('button_press_event', lambda event: avg_waves.on_click(self,event))
                    self.canvas_label_low.setText('average waveforms')
                    self.main_cid = None
                    self.canvas_label.setText('isi histogram')
                elif plot == 2:
                    self.mid_cid = self.midfigure.canvas.mpl_connect('button_press_event', lambda event: sort_2d.on_click(self,event))
                    self.canvas_label_mid.setText('2d parameters')
                    self.low_cid = self.lowfigure.canvas.mpl_connect('button_press_event', lambda event: wave_cut.on_press(self,event))
                    self.canvas_label_low.setText('waveforms')
                    self.main_cid = self.plot_figs['avg_wave'].canvas.mpl_connect('button_press_event', lambda event: avg_waves.on_click(self,event))
                    self.canvas_label.setText('average waveforms')
                    self.top_cid = None
                    self.canvas_label_top.setText('isi histogram')
                elif plot == 3:
                    self.low_cid = self.lowfigure.canvas.mpl_connect('button_press_event', lambda event: sort_2d.on_click(self,event))
                    self.canvas_label_low.setText('2d parameters')
                    self.main_cid = self.mainfigure.canvas.mpl_connect('button_press_event', lambda event: wave_cut.on_press(self,event))
                    self.canvas_label.setText('waveforms')
                    self.top_cid = self.plot_figs['avg_wave'].canvas.mpl_connect('button_press_event', lambda event: avg_waves.on_click(self,event))
                    self.canvas_label_top.setText('average waveforms')
                    self.mid_cid = None
                    self.canvas_label_mid.setText('isi histogram')

''''''''''''''''''''''''''''''''''''''''''''''''''''''
######################################################
''''''''''''''''''''''''''''''''''''''''''''''''''''''
        
if __name__ == '__main__':
    #create a QApplication if one doesn't already exist
    app = QApplication.instance()
    if app == None:
        app = QApplication(['/Users/Patrick/anaconda/lib/python2.7/site-packages/spyderlib/widgets/externalshell/start_ipython_kernel.py'])
    
    #create and show the main window
    frame = MainWindow()
    frame.show()
    
    #exit the app when we're all done
    sys.exit(app.exec_())