# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 12:37:38 2017

spike sort self

@author: Patrick
"""

import os
os.environ['QT_API'] = 'pyside'
import sys
import pickle
import time
import numpy as np
from OpenEphys import loadSpikes
#import matplotlib.pyplot as plt
from matplotlib.widgets import LassoSelector
from matplotlib import path
from matplotlib import colors as mplcolors


     
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
        mainlayout = QGridLayout()

        #make matplotlib plotting frame along with Next/Back buttons, collect
        plot_frame,self.maincanvas,self.canvas_label = self.setup_mpl_canvas()
        plot_frame_top,self.topcanvas,self.canvas_label_top,plot_frame_mid,self.midcanvas,self.canvas_label_mid,plot_frame_low,self.lowcanvas,self.canvas_label_low = self.setup_side_canvases()
        params_layout,param_Frame,peaks_button,valleys_button,energy_button = self.setup_param_buttons()
        rb_layout,rb_frame,new_button,delete_button,merge_button = self.setup_random_buttons()
        clusters_layout,clusters,c0_button = self.setup_cluster_buttons()

        #add the matplotlib NavigationToolbar above plotting canvas
        self.toolbar = NavigationToolbar(self.maincanvas, self)
        self.toolbar.setGeometry(QRect(self.screen_width*.1, self.screen_height*.03, self.screen_width*.25, self.screen_height*.07))

        #add every widget to the main 
        mainlayout.addWidget(plot_frame)
        mainlayout.addWidget(self.toolbar)
        mainlayout.addWidget(plot_frame_top)
        mainlayout.addWidget(plot_frame_mid)
        mainlayout.addWidget(plot_frame_low)

        #create a QMenuBar and set geometry
        self.menubar = QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, self.screen_width*.5, self.screen_height*.03))
        #set the QMenuBar as menu bar for main window
        self.setMenuBar(self.menubar)
        
        self.setup_file_menu()
        self.setup_view_menu()
        
        peaks_button.clicked.connect(self.plot_peaks)
        valleys_button.clicked.connect(self.plot_valleys)
        energy_button.clicked.connect(self.plot_energy)
        
        self.showMaximized()
        
    def setup_file_menu(self):
        fileMenu = QMenu('&File',self)
        self.menubar.addMenu(fileMenu)
        
        fileMenu.addAction('&Open spike file', self.open_file, 'Ctrl+O')
        fileMenu.addAction('&Save spike file', self.save_file, 'Ctrl+S')
        fileMenu.addAction('&Save timestamp file', self.save_ts, 'Ctrl+T')
        
    def setup_view_menu(self):
        viewMenu = QMenu('&View',self)
        self.menubar.addMenu(viewMenu)
        
        viewMenu.addAction('&Time plot', self.time_plot, 'Ctrl+F4')

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
        new_button = QPushButton('new cluster') 
        delete_button = QPushButton('delete cluster')
        merge_button = QPushButton('merge')
        #add to layout
        #rb_layout.addWidget(rb_label)        
        rb_layout.addWidget(new_button)
        rb_layout.addWidget(delete_button)
        rb_layout.addWidget(merge_button)
        
        return rb_layout,rb,new_button,delete_button,merge_button  

    def setup_cluster_buttons(self):
        #make QFrame
        clusters = QFrame(self)
        #make and set label
        clusters_label = QLabel()
        clusters_label.setText('clusters')
        #set gemoetry and color
        clusters.setGeometry(QRect(self.screen_width*.36, self.screen_height*.03, self.screen_width*.34, self.screen_height*.07))
        clusters.setObjectName("clustersWidget")
        clusters.setStyleSheet("#clustersWidget {background-color:gray;}")
        #create and set layout
        clusters_layout = QHBoxLayout()
        clusters.setLayout(clusters_layout)
        #make labview checkbox
        c0_button = QPushButton('0')
        c0_button.setCheckable(True)
        #add to layout
        clusters_layout.addWidget(clusters_label)        
        clusters_layout.addWidget(c0_button)
        clusters_layout.addStretch(1)
        
        return clusters_layout,clusters,c0_button
        
    
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
        peaks_button = QPushButton('peaks')
        valleys_button = QPushButton('valleys')
        energy_button = QPushButton('energy')

        #add to layout
        params_layout.addWidget(params_label)        
        params_layout.addWidget(peaks_button)
        params_layout.addWidget(valleys_button)
        params_layout.addWidget(energy_button)
        params_layout.addStretch(1)
        
        return params_layout,params,peaks_button,valleys_button,energy_button
        
    def open_file(self):
        fname = QFileDialog.getOpenFileName(self, 'Open Spike File', '','Openephys spike files (*.spikes)')
        spike_data = loadSpikes(fname[0])
        
        waveforms = np.swapaxes(spike_data['spikes'],1,2)
        self.peaks = sort_2d.find_peaks(waveforms)
        self.valleys = sort_2d.find_valleys(waveforms)
        self.energy = self.peaks**2
        
        self.num_spikes = len(waveforms)
        self.waveforms = np.swapaxes(waveforms,0,1)
        self.canvas_label.setText('2d peak view')
        self.canvas_label_top.setText('waveforms')
        
        self.current_clust = 1
        self.clusts = np.zeros(self.num_spikes)
        
        sort_2d.plot_it(self.peaks,self.num_spikes,self)
        self.wave_axes,self.wave_lines=wave_cut.plot_waveforms(self.waveforms,self)
        
        
        
        
    def plot_peaks(self):
        self.mainfigure.clear()
        sort_2d.plot_it(self.peaks,self.num_spikes,self)
        
    def plot_valleys(self):
        self.mainfigure.clear()
        sort_2d.plot_it(self.valleys,self.num_spikes,self)
        
    def plot_energy(self):
        self.mainfigure.clear()
        sort_2d.plot_it(self.energy,self.num_spikes,self)
        
    def onselect1(self,verts):
        p = path.Path(verts)
        ind = p.contains_points(self.points1, radius=0)
        self.clusts[ind] = self.current_clust
        self.lines=sort_2d.update_colors(self.lines,self.clusts)
    
        self.mainfigure.canvas.draw_idle()
        
    def onselect2(self,verts):
        p = path.Path(verts)
        ind = p.contains_points(self.points2, radius=0)
        self.clusts[ind] = self.current_clust
        self.lines=sort_2d.update_colors(self.lines,self.clusts)
        self.mainfigure.canvas.draw_idle()
        
    def onselect3(self,verts):
        p = path.Path(verts)
        ind = p.contains_points(self.points3, radius=0)
        self.clusts[ind] = self.current_clust
        self.lines=sort_2d.update_colors(self.lines,self.clusts)
        self.mainfigure.canvas.draw_idle()
        
    def onselect4(self,verts):
        p = path.Path(verts)
        ind = p.contains_points(self.points4, radius=0)
        self.clusts[ind] = self.current_clust
        self.lines=sort_2d.update_colors(self.lines,self.clusts)
        self.mainfigure.canvas.draw_idle()
        
    def onselect5(self,verts):
        p = path.Path(verts)
        ind = p.contains_points(self.points5, radius=0)
        self.clusts[ind] = self.current_clust
        self.lines=sort_2d.update_colors(self.lines,self.clusts)
        self.mainfigure.canvas.draw_idle()
        
    def onselect6(self,verts):
        p = path.Path(verts)
        ind = p.contains_points(self.points6, radius=0)
        self.clusts[ind] = self.current_clust
        self.lines=sort_2d.update_colors(self.lines,self.clusts)
        self.mainfigure.canvas.draw_idle()
        
    def save_file(self):
        x=1
        
    def save_ts(self):
        x=2
        
    def time_plot(self):
        x=3
        
    def initial_plots(self):
        x=4
        
    def setup_mpl_canvas(self):
        ''' set up the matplotlib plotting canvas '''
        
        #create QFrame with parent self
        plot_frame = QFrame(self)
        #make a label for the canvas
        canvas_label = QLabel()
        #make label empty for now
        canvas_label.setText('')
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
        plot_layout.addWidget(canvas_label)
        plot_layout.addWidget(self.maincanvas)

        #return frames and buttons
        return plot_frame,self.maincanvas,canvas_label
    
    def setup_side_canvases(self):
        ''' set up bonus plotting canvases '''
        
        #create QFrame with parent self
        plot_frame_top = QFrame(self)
        #make a label for the canvas
        canvas_label_top = QLabel()
        #make label empty for now
        canvas_label_top.setText('')
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
        plot_layout_top.addWidget(canvas_label_top)
        plot_layout_top.addWidget(self.topcanvas)
        
        #create QFrame with parent self
        plot_frame_mid = QFrame(self)
        #make a label for the canvas
        canvas_label_mid = QLabel()
        #make label empty for now
        canvas_label_mid.setText('')
        #set geometry
        plot_frame_mid.setGeometry(QRect(self.screen_width*.72, self.screen_height*.4, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_mid.setObjectName("mid_canvas_widget")
        #give it a cool color
        plot_frame_mid.setStyleSheet("#mid_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        plot_layout_mid = QVBoxLayout()
        plot_frame_mid.setLayout(plot_layout_mid)
        #create a matplotlib figure for plotting data to
        self.mid_figure = Figure()
        #create a canvas to show the figure on
        self.midcanvas = FigureCanvas(self.mid_figure)
        #add canvas and label to layout
        plot_layout_mid.addWidget(canvas_label_mid)
        plot_layout_mid.addWidget(self.midcanvas)
        
        #create QFrame with parent self
        plot_frame_low = QFrame(self)
        #make a label for the canvas
        canvas_label_low = QLabel()
        #make label empty for now
        canvas_label_low.setText('')
        #set geometry
        plot_frame_low.setGeometry(QRect(self.screen_width*.72, self.screen_height*.7, self.screen_width*.23, self.screen_height*.25))
        #name the QFrame so we can give it a cool color
        plot_frame_low.setObjectName("low_canvas_widget")
        #give it a cool color
        plot_frame_low.setStyleSheet("#low_canvas_widget {background-color:white;}") 
        #give the QFrame a layout
        plot_layout_low = QVBoxLayout()
        plot_frame_low.setLayout(plot_layout_low)
        #create a matplotlib figure for plotting data to
        self.low_figure = Figure()
        #create a canvas to show the figure on
        self.lowcanvas = FigureCanvas(self.low_figure)
        #add canvas and label to layout
        plot_layout_low.addWidget(canvas_label_low)
        plot_layout_low.addWidget(self.lowcanvas)

        #return frames and buttons
        return plot_frame_top,self.topcanvas,canvas_label_top,plot_frame_mid,self.midcanvas,canvas_label_mid,plot_frame_low,self.lowcanvas,canvas_label_low

        
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