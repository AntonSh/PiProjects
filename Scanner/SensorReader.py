#!/usr/bin/python
# logging sensor data to a local file
import subprocess
import time
import sys
import Utils

readTemp = "/home/mray/PiProjects/Sensor/readtemp"

pins = []

def setup(sensorPins):	
	global pins
	pins = sensorPins
	Utils.log("T, " + ", ".join(map((lambda x: "H{}, T{}".format(x,x)), pins)))


def getReadings():	
	global pins
	output = subprocess.check_output([readTemp, "-gpio"]+(map(str, pins))).strip()
	
        line = "[{}]".format(', '.join(output.split('\n')))
	val = eval(line)
	dataDict = dict(map((lambda l: (l['pin'], l)), val))
	fileLine = time.strftime("%c") + ", " +  ", ".join(map((lambda x: "{}, {}".format(dataDict[x]['temp'],dataDict[x]['humidity'])), pins)) 
	Utils.log(fileLine)
	return val
