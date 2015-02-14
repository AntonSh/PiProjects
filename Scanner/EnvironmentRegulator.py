#!/usr/bin/python
import subprocess
import time
import sys
import signal 
import argparse
import sqlite3 as lite
from datetime import datetime, date

import GPIOControl
import SensorReader
import Utils

# constants
pinModes = ["off", "ON"]

logFile = "../logs/control.log"
dataStream = "../Data/sensor_stream.db"
controlFile = "../Data/contol_steam.db"

# running state
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

def updateDatabase():
	try:
		con = lite.connect(controlFile)

		timestamp = int(time.time())
		cur = con.cursor()  

		rows = [[timestamp, "compressor", 1*currentPumpState], 
				[timestamp, "humidifier", 1*currentHumidifierState]]

		for row in rows:
			print row
			cur.execute("insert into control_log values(?,?,?)", row)

		con.commit()
	except lite.Error, e:
		if con:
			con.rollback()

		print "Error %s:" % e.args[0]

	except:
		print sys.exc_info()

	finally:
		if con:
			con.close() 

def runControl():
	try:
		Utils.log(time.strftime("%c") + ", running control");

		con = lite.connect(dataStream)
		cur = con.cursor()

		timestamp = int(time.time()) - historyWindowSec
		cur.execute("select avg(temperature), avg(humidity), count(*) from sensor_log where time_stamp > ?", [timestamp])
		result = cur.fetchall()
		samples = result[0][2]

		T = result[0][0]
		RH = result[0][1]

		if samples == 0:
			Utils.log(time.strftime("%c") + ", No environment data detected, shutting down equipment!");
			
			switchHumidifier(False)
			switchPump(False)
			return


		checkT(T)
		checkRH(RH)
		
	finally:
		updateDatabase()
		Utils.log(time.strftime("%c") + ", done running control ");

		if(con != None):
			con.close()

# Gracefull shutdown
def signal_handler(signal, frame):
	print('Caught signal, exiting')
	switchHumidifier(False)
	switchPump(False)
      
        sys.exit(0)



# input parameters
parser = argparse.ArgumentParser(description='Environment regulator process controls humidifier and refregirator compressor pump uses data from Sqlite database')
parser.add_argument('-rh',    type=int, help='Target relative humidity of the environment',           required = True)
parser.add_argument('-rhDev', type=int, help='Acceptable relative humidity deviation from target rh', default=2)

parser.add_argument('-t',     type=int, help='Target environment temperature',                        required = True)
parser.add_argument('-tDev',  type=int, help='Accptable environment temperature deviation',           default=1)

parser.add_argument('-pumpPin',    type=int, help='GPIO pin that controls refregirator pump relay',   required = True)
parser.add_argument('-pumpPinMode', choices=pinModes, help='Pump pin state when pump is OFF',                 default = pinModes[0])

parser.add_argument('-humidifierPin', type=int, help='GPIO pin that controls humidifier',             required = True)
parser.add_argument('-humidifierPinMode', choices=pinModes, help='Humidifier pin state when humidifier is OFF', default = pinModes[0])

parser.add_argument('-frequency', type=int, help='Sensor data refresh frequency (seconds)',       default = 30)
parser.add_argument('-avgWindow', type=int, help='Sensor data averagin period (seconds)',         default = 60)

args = parser.parse_known_args()[0]


# TODO make this parameters updated on flight using data stored in Sqlite
targetRH = args.rh
rhDev = args.rhDev

targetTemp = args.t
tempDev = args.tDev

pumpPin = args.pumpPin
pumpPinMode = args.pumpPinMode

humPin = args.humidifierPin
humPinMode = args.humidifierPinMode

refreshSec = args.frequency
historyWindowSec = args.avgWindow

print "Running Environment Regulator \n Temp: {}; Temp Dev {}; \n RH {}; RH Dev {};".format(targetTemp, tempDev, targetRH, rhDev);
print "Pump pin {}; Pump pin mode {}; Humidifier pin {}; Humidifier pin mode {};".format(pumpPin, pumpPinMode, humPin, humPinMode);
print "Refresh Rate {}; Averaging window {};".format(refreshSec, historyWindowSec);

Utils.setupLog(logFile)
gpioConfig = {
	pumpPin:pinModes.index(pumpPinMode),
	humPin :pinModes.index(humPinMode)
}

GPIOControl.setup(gpioConfig)
signal.signal(signal.SIGINT, signal_handler)

while True:

        try:
		runControl()
            				
        except:
                print sys.exc_info()

        time.sleep(refreshSec)
