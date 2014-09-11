#!/usr/bin/python
# logging sensor data to a local file
import subprocess
import time

pins = [22, 18, 4]
readTemp = "/home/mray/PiProjects/Sensor/readtemp"
outputfile = "sensor.log.csv"
delaySec = 10

def monitorTemperature():	
	output = subprocess.check_output([readTemp, "-gpio"]+(map(str, pins))).strip()
	processOutput(output)	

def processOutput(output):
        line = "[{}]".format(', '.join(output.split('\n')))
	val = eval(line)
	dataDict = dict(map((lambda l: (l['pin'], l)), val))
	fileLine = time.strftime("%c") + ", " + ", ".join(map((lambda x: "{}, {}".format(dataDict[x]['temp'],dataDict[x]['humidity'])), pins)) 
	appendToFile(fileLine)

def appendToFile(line):
	print line
	with open(outputfile, "a") as myfile:
	    myfile.write(line + '\n')

print ("Temperature logging started")
appendToFile("T, " + ", ".join(map((lambda x: "H{}, T{}".format(x,x)), pins)))

while True:
	monitorTemperature()
	time.sleep(delaySec)
