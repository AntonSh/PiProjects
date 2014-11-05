#!/usr/bin/python
import subprocess
import time
import sys

import GPIOControl
import SensorReader
import Utils

pinModes = ["off", "ON"]

targetRH = 80
rhDev = 2.5

targetTemp = 15
tempDev = 1

pumpPin = 18
humPin = 23
sensorPins = [2, 17]
logFile = "/home/ahtoxa/control.log"

refreshSec = 10

currentPumpState = False
currentHumidifierState = False

def switchHumidifier(state):
	global currentHumidifierState
	if state <> currentHumidifierState and GPIOControl.switchPin(humPin, state):
		currentHumidifierState = state

def switchPump(state):
	global currentPumpState
	if state <> currentPumpState and GPIOControl.switchPin(pumpPin, state):
		currentPumpState = state

def runAnalysis():
	value = SensorReader.getReadings() 
        temp = [x["temp"] for x in value]
       	avgTemp = sum(temp) / len(temp)

        desiredPumpState = avgTemp > targetTemp

	if not (targetTemp - tempDev <= avgTemp <= targetTemp + tempDev) and (desiredPumpState <> currentPumpState):		
	        Utils.log(time.strftime("%c") + ", requested pump " + pinModes[1*desiredPumpState]);
		switchPump(desiredPumpState)

        rh = [x["humidity"] for x in value]
	avgRH = sum(rh) / len(rh)
	desiredHumidifierState = avgRH < targetRH

	if not (targetRH - rhDev <= avgRH <= targetRH + rhDev) and (desiredHumidifierState <> currentHumidifierState):
                Utils.log(time.strftime("%c") + ", requested humidifier " + pinModes[1*desiredHumidifierState]);
		switchHumidifier(desiredHumidifierState)

	Utils.log(time.strftime("%c") + ", pump " + pinModes[1*currentPumpState] +  ", hum " + pinModes[1*currentHumidifierState]);


Utils.setupLog(logFile)
SensorReader.setup(sensorPins)
GPIOControl.setup([pumpPin, humPin])


while True:

        try:
		runAnalysis()
            				
        except:
                print sys.exc_info()

        time.sleep(refreshSec)
