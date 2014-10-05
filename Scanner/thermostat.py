#!/usr/bin/python
import subprocess
import time
import sys

import GPIOControl
import SensorReader
import Utils

targetTemp = 15
tempDev = 1

pumpPin = 23 #18
sensorPins = [2, 17]
logFile = "/home/ahtoxa/control.log"

refreshSec = 10

def switchPump(state):
	print GPIOControl.switchPin(pumpPin, state)

Utils.setupLog(logFile)
SensorReader.setup(sensorPins)
GPIOControl.setup(pumpPin)

blah = False

while True:

        try:
                value = SensorReader.getReadings()
                print value
		switchPump(blah)
		blah = not blah
        except:
                print sys.exc_info()

        time.sleep(refreshSec)
