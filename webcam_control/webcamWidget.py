# -*- coding: utf-8 -*-

import numpy as np


from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import cv2
from PyQt5.QtWidgets import QFileDialog

from webcamSimulator import WebcamSimulator
from matplotlibWindow import MatplotlibWindow
from tifffile import tifffile


class WebcamManager(QtGui.QWidget):
    """class handling a webcam and displaying its frames on screen
    
    :param TempestaGUI main: the main GUI.
    """
    def __init__(self,main, simulation = True):
        super().__init__()
        self.simulation = simulation
        if self.simulation:
            self.webcam = WebcamSimulator()
        else:
            self.webcam=cv2.VideoCapture(1)
        
        self.main=main
        self.frameStart = (0, 0)
        self.title=QtGui.QLabel()
        self.title.setText("Webcam")
        self.title.setStyleSheet("font-size:18px")
        
        self.display = MatplotlibWindow()
        self.curframe = np.random.rand(50,50)
#        These attributes are the widgets which will be used in the main script
        self.imageWidget = pg.GraphicsLayoutWidget()
        
        self.line_hor = pg.InfiniteLine(pos=0,angle=90,movable=True)
        self.line_vert = pg.InfiniteLine(pos=0,angle=0,movable=True)
      # Liveview functionality
        self.liveviewButton = QtGui.QPushButton('LIVEVIEW')
        self.liveviewButton.setStyleSheet("font-size:18px")
        self.liveviewButton.setCheckable(True)
        self.liveviewButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                          QtGui.QSizePolicy.Expanding)
        self.liveviewButton.clicked.connect(self.liveview)      #Link button click to funciton liveview
        self.liveviewButton.setEnabled(True)
        
        self.exposureButton = QtGui.QLineEdit('-15')        
        self.exposureLabel=QtGui.QLabel()
        self.exposureLabel.setText("exposure time:")
        
        self.savePushbutton = QtGui.QPushButton("Save frame")
        self.savePushbutton.clicked.connect(self.save_prompt)
        
        self.viewtimer = QtCore.QTimer()
        self.viewtimer.timeout.connect(self.updateView)
        
        self.viewCtrlLayout = QtGui.QGridLayout()
        self.viewCtrlLayout.addWidget(self.title,0,0)
        self.viewCtrlLayout.addWidget(self.imageWidget,1,0,3,4)
        self.viewCtrlLayout.addWidget(self.liveviewButton, 5, 0, 1, 1)
        self.viewCtrlLayout.addWidget(self.exposureLabel,5,1,1,1)
        self.viewCtrlLayout.addWidget(self.exposureButton,5,2,1,1)
        self.viewCtrlLayout.addWidget(self.savePushbutton,5,3,1,1)
        
        self.viewCtrlLayout.addWidget(self.display,1,5,3,3)
        
        self.setLayout(self.viewCtrlLayout)
        
        self.lvworker = LVWorker(self, self.webcam)
        self.exposureButton.textChanged.connect(self.lvworker.setExposure)
        
        self.lvworker.newframeSignal.connect(self.setImage)

        # Image Widget
        #self.imageWidget.addItem(self.line)
        
        self.roi = pg.LineSegmentROI([[10, 64], [120,64]], pen='r')
        self.roi.sigRegionChanged.connect(self.update_rois)
        
        #if self.imageNumber==0:
        
        self.vb = self.imageWidget.addViewBox(row=1, col=1)
        # self.vb.setMouseMode(pg.ViewBox.RectMode)
        self.img = pg.ImageItem()
        self.img.translate(-0.5, -0.5)
        self.vb.addItem(self.img)
        self.vb.addItem(self.line_vert)
        self.vb.addItem(self.line_hor)
        self.vb.addItem(self.roi)
        self.vb.setAspectLocked(True)
        self.img.setImage(self.curframe)

    def setImage(self,array):
        """:param numpy.ndarray array: the image to display"""
        self.img.setImage(array.astype(np.float))
        self.curframe = array
    def liveview(self):
        """Method called when the LiveviewButton is pressed. Starts or Stops Liveview."""
        if self.liveviewButton.isChecked():
            self.liveviewStart()

        else:
            self.liveviewStop()

    def liveviewStart(self):
        """Starts liveview"""
        self.lvworker.start()


    def liveviewStop(self):
        """Stops Liveview"""
        self.lvworker.stop()


    def updateView(self):
        """ Image update while in Liveview mode
        Not used anymore. Kept for archeologic purpose.
        """
        osef,frame=self.webcam.read()
        self.img.setImage(np.rot90(frame), autoLevels=False, autoDownsample = False) 

    def closeEvent(self, *args, **kwargs):
        self.webcam.release()
        
        
    def update_rois(self,roi,axes = None,*args,**kwargs):

        
        data=[]
        names = []
        unit = "pixels"
        print(self.img.data)
        print(self.img)
        data = self.roi.getArrayRegion(self.curframe, self.img, axes=(0,1))
        psize = 1
            
        #if axes is None:
        fig = self.display.figure
    
        fig.clf()
        ax = fig.add_subplot(1,1,1)

        """if self.fitButton.isChecked():
            self.fit_data(ax=ax)"""
                
        ax.plot(np.arange(data.size)*psize,data)
            
        ax.set_xlabel("Distance ("+unit+")")
        ax.set_ylabel("Counts")
    
        self.display.plot()
    
    def save_prompt(self):
        
        fdiag, _ = QFileDialog.getSaveFileName(self,
                    "Select output file name",
                    "image","Tiff files (*)")
        if fdiag:
            self.save(fdiag)
    def save(self,name):
        if name[-4:]!=".tif":
            name+=".tif"
        data = self.curframe.astype(float)/self.curframe.max()
        data = (data*255).astype(np.uint8)
        tifffile.imsave(name,data)
        
class LVWorker(QtCore.QThread):
    """Thread acquiring images from the webcam and sending it to the display widget
    
    :param WebcamManager webcam: the webcam widget using this thread
    :param cv2.VideoCapture webcam: the opencv instance of the webcam emitting the frames."""
    newframeSignal = QtCore.pyqtSignal(np.ndarray)
    def __init__(self, main, webcam, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main = main
        self.webcam = webcam
        self.running = False
        
    def run(self):
        """Runs the worker. Reads a frame from the webcam every 10ms and sends it to
        the display with a Qt Signal"""
        self.vtimer = QtCore.QTimer()

        self.running = True
        import time
        while(self.running):
            osef,frame = self.webcam.read()
            frame = np.rot90(frame)
            self.newframeSignal.emit(frame )
            time.sleep(0.01)

    def setExposure(self,value):
        """ :param float value: the new exposure time parameter
        """
        try:
            exp_time=float(value)
        except:
            return
        self.webcam.set(15,exp_time)
        
    def stop(self):
        """stops the frame acquisition"""
        if self.running:
#            self.vtimer.stop()
            self.running = False
            print('Acquisition stopped')
        else:
            print('Cannot stop when not running (from LVThread)')
            
        
if __name__ == '__main__':
    app = QtGui.QApplication([])
    webm=WebcamManager("train")
    webm.show()
    app.exec_()