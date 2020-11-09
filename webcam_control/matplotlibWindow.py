#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 15:31:43 2020

@author: aurelien
"""


import matplotlib.pyplot as plt
import numpy as np
from matplotlib_scalebar.scalebar import ScaleBar
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QCheckBox, QLabel

from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.image import AxesImage

class FittingWidget(QWidget):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fitCheckBox = QCheckBox("Gaussian fit")
        self.fitResultsLabel = QLabel("Fit Results")
        self.fitResultsValues = QLabel("")
        
        layout = QtGui.QGridLayout()
        layout.addWidget(self.fitCheckBox,0,0)
        layout.addWidget(self.fitResultsLabel,0,1)
        layout.addWidget(self.fitResultsValues,0,2)
        self.setLayout(layout)
        
class MatplotlibWindow(QtGui.QDialog):
    plot_clicked = QtCore.Signal(int)
    back_to_plot = QtCore.Signal()
    image_clicked = QtCore.Signal(np.ndarray)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # a figure instance to plot on
        self.figure = Figure()
        
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.fittingWidget = FittingWidget()
        # set the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.fittingWidget)
        self.setLayout(layout)

        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.canvas.mpl_connect('pick_event', self.onpick)
        
    def onclick(self,event):
        try:
            if event.dblclick and event.button==1:
                ns = self.figure.axes[0].get_subplotspec().get_gridspec().get_geometry()
                assert(ns[0]==ns[1])
                ns = ns[0]
                
                            
                #gets the number of the subplot that is of interest for us
                n_sub = event.inaxes.rowNum*ns + event.inaxes.colNum
                self.figure.clf()
                self.plot_clicked.emit(n_sub)
            elif event.button==3: 
               self.back_to_plot.emit()
        except:
           pass
       
    def onpick(self,event):
        artist = event.artist
        if isinstance(artist, AxesImage):
            im = artist
            A = im.get_array()
            print('image clicked', A.shape)
            self.image_clicked.emit(A)
            
    def plot(self):
        self.canvas.draw()