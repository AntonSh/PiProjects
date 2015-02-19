#!/usr/bin/python
import subprocess
import time
import sys
import signal 
import argparse
import sqlite3 as lite
from datetime import datetime, date

import PWMThread
import GPIOControl
import SensorReader
import Utils

# constants
pinModes = ["off", "ON"]

Default_RH = 40
Default_Temp = 18

logFile = "../logs/control.log"
dataStream = "../Data/sensor_stream.db"
controlFile = "../Data/control_stream.db"

# running state
currentPumpState = False
currentHumidifierState = False

# input parameters
parser = argparse.ArgumentParser(description='Environment regulator process controls humidifier and refregirator compressor pump uses data from Sqlite database')
parser.add_argument('-rhDev', type=int, help='Acceptable relative humidity deviation from target rh', default=2)

parser.add_argument('-tDev',  type=int, help='Accptable environment temperature deviation',           default=1)

parser.add_argument('-pumpPin',    type=int, help='GPIO pin that controls refregirator pump relay',   required = True)
parser.add_argument('-pumpPinMode', choices=pinModes, help='Pump pin state when pump is OFF',         default = pinModes[0])

parser.add_argument('-humidifierPin', type=int, help='GPIO pin that controls humidifier',             required = True)
parser.add_argument('-humidifierPinMode', choices=pinModes, help='Humidifier pin state when humidifier is OFF', default = pinModes[0])

parser.add_argument('-frequency', type=int, help='Sensor data refresh frequency (seconds)',       default = 30)
parser.add_argument('-avgWindow', type=int, help='Sensor data averagin period (seconds)',         default = 60)

def switchHumidifier(state):
	global currentHumidifierState
	if state <> currentHumidifierState and GPIOControl.switchPin(humPin, state):
		currentHumidifierState = state

def switchPump(state):
	global currentPumpState
	if state <> currentPumpState and GPIOControl.switchPin(pumpPin, state):
		currentPumpState = state

def checkT(temp, targetTemp):
	desiredPumpState = temp > targetTemp

	if not (targetTemp - tempDev <= temp <= targetTemp + tempDev) and (desiredPumpState <> currentPumpState):		
		Utils.log(time.strftime("%c") + ", requested pump " + pinModes[1*desiredPumpState]);
		switchPump(desiredPumpState)

def checkRH(rh, targetRH):
	desiredHumidifierState = rh < targetRH

	if not (targetRH - rhDev <= rh <= targetRH + rhDev) and (desiredHumidifierState <> currentHumidifierState):
		Utils.log(time.strftime("%c") + ", requested humidifier " + pinModes[1*desiredHumidifierState]);
		switchHumidifier(desiredHumidifierState)

def findTargetParameters():

	temp = Default_Temp
	rh 	 = Default_RH

	try:
		con = lite.connect(controlFile)

		timestamp = int(time.time())
		cur = con.cursor()  

		cur.execute("select * from control_target where time_stamp < ? order by time_stamp desc limit 1" , [timestamp])
		pastTarget = cur.fetchall()

		cur.execute("select * from control_target where time_stamp > ? order by time_stamp asc limit 1" , [timestamp])
		futureTarget = cur.fetchall()

		futureTimestamp = futureTarget[0][0]
		pastTimestamp = pastTarget[0][0]

		scale = (1.0 * timestamp - pastTimestamp) / (futureTimestamp - pastTimestamp)

		futureTemp = futureTarget[0][1]
		futureRH   = futureTarget[0][2]

		pastTemp   = pastTarget[0][1]
		pastRH 	   = pastTarget[0][2]

		temp  = pastTemp + scale * (futureTemp - pastTemp)
		rh = pastRH + scale * (futureRH - pastRH)				

		Utils.log(time.strftime("%c") + ", running control, target T: {:10.1f}, RH {:10.1f}%".format(temp, rh));

	except lite.Error, e:
		if con:
			con.rollback()

		print "Error %s:" % e.args[0]

	except:
		print sys.exc_info()

	finally:
		if con:
			con.close() 

	return temp, rh 

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

def runControl(targetT, targetRH):
	try:
		Utils.log(time.strftime("%c") + ", running control");

		con = lite.connect(dataStream)
		cur = con.cursor()

		timestamp = int(time.time()) - historyWindowSec
		cur.execute("select temperature, humidity from sensor_log where time_stamp > ?", [timestamp])
		result = cur.fetchall()
		samples = result[0][2]

		T = result[0][0]
		RH = result[0][1]

		if samples == 0:
			Utils.log(time.strftime("%c") + ", No environment data detected, shutting down equipment!");
			
			switchHumidifier(False)
			switchPump(False)
			return

		checkT(T, targetT)
		checkRH(RH, targetRH)
		
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

args = parser.parse_known_args()[0]


rhDev = args.rhDev

tempDev = args.tDev

pumpPin = args.pumpPin
pumpPinMode = args.pumpPinMode

humPin = args.humidifierPin
humPinMode = args.humidifierPinMode

refreshSec = args.frequency
historyWindowSec = args.avgWindow

print "Running Environment Regulator\n Temp Dev {}; RH Dev {};".format(tempDev, rhDev);
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
        	targetT, targetRH = findTargetParameters()
        	runControl(targetT, targetRH)
            				
        except:
                print sys.exc_info()

        time.sleep(refreshSec)
