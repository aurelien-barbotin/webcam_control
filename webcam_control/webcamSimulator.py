#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 15:22:15 2020

@author: aurelien
"""
import numpy as np

class WebcamSimulator(object):
    def __init__(self, *args, **kwargs):
        self.image = np.random.rand(50,50,3)
        
    def read(self):
        return None, np.random.rand(50,50,3)
    
    def set(self, *args,**kwargs):
        pass
    
    def release(self):
        pass