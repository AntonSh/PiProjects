#!/usr/bin/python
import subprocess
import time
import sys
import signal 

import GPIOControl
import SensorReader
import Utils
import sqlite3 as lite
from datetime import datetime, date

pinModes = ["off", "ON"]

targetRH = 10
rhDev = 2.5

targetTemp = 10
tempDev = 1

pumpPin = 18
humPin = 23

logFile = "../logs/control.log"
dataStream = "../Data/sensor_stream.db"

refreshSec = 30
historyWindowSec = 60


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

def checkT(temp):
	desiredPumpState = temp > targetTemp

	if not (targetTemp - tempDev <= temp <= targetTemp + tempDev) and (desiredPumpState <> currentPumpState):		
	        Utils.log(time.strftime("%c") + ", requested pump " + pinModes[1*desiredPumpState]);
		switchPump(desiredPumpState)

def checkRH(rh):
	desiredHumidifierState = rh < targetRH

	if not (targetRH - rhDev <= rh <= targetRH + rhDev) and (desiredHumidifierState <> currentHumidifierState):
                Utils.log(time.strftime("%c") + ", requested humidifier " + pinModes[1*desiredHumidifierState]);
		switchHumidifier(desiredHumidifierState)

def runControl():
	try:
		Utils.log(time.strftime("%c") + ", running control");

		con = lite.connect(dataStream)
		cur = con.cursor()

		timestamp = int(time.time()) - historyWindowSec
		cur.execute("select avg(temperature), avg(humidity) from sensor_log where time_stamp > ?", [timestamp])
		result = cur.fetchall()
		T = result[0][0]
		RH = result[0][1]

		checkT(T)
		checkRH(RH)
		
	finally:
		Utils.log(time.strftime("%c") + ", done running control ");

		if(con != None):
			con.close()

# Gracefull shutdown
def signal_handler(signal, frame):
	print('Caught signal, exiting')
	switchHumidifier(False)
	switchPump(False)
      
        sys.exit(0)

Utils.setupLog(logFile)
GPIOControl.setup({pumpPin:0, humPin:1})
signal.signal(signal.SIGINT, signal_handler)

while True:

        try:
		runControl()
            				
        except:
                print sys.exc_info()

        time.sleep(refreshSec)
