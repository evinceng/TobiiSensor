# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 12:08:14 2018

@author: TTTT
"""
import Sensor

class DataParsedSensor(Sensor.Sensor):
    
    def parseData(self, data):
        for i in range (0, 30):
            print 'The data is parsed '
        return data