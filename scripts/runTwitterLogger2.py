#!/usr/bin/python
import time
import sys
import os
import sqlite3 as lite
from twitter import *
from datetime import datetime, date
import matplotlib
import matplotlib.dates as md
matplotlib.use('Agg')

import matplotlib.pyplot as plt

token = open('/home/ahtoxa/twitter/token', 'r').readline()
token_key = open('/home/ahtoxa/twitter/token_key', 'r').readline()
con_secret = open('/home/ahtoxa/twitter/con_secret', 'r').readline()
con_secret_key = open('/home/ahtoxa/twitter/con_secret_key', 'r').readline()

dataStream = "../Data/sensor_stream.db"
controlStream = "../Data/control_stream.db"
logDirectory = "../logs"

refreshSec = 600
labels = { 2 : "Temperature", 3 : "Humidity" }

def queryLogData(tableName, timestamp):
	try:
		con = lite.connect(dataStream)
		cur = con.cursor()

		query = "select * from {} where time_stamp > ?".format(tableName)
		cur.execute(query, [timestamp])
		return cur.fetchall()

	finally:
		if(con != None):
			con.close()

def runReport():	
	timestamp = int(time.time()) - refreshSec
	result = queryLogData("sensor_log", timestamp)

	if len(result) == 0:
		return ("No data!", "error picture")

	sensors = set([x[1] for x in result])
	print "Found sensors {}".format(sensors)
	
	axis = createPlot()

	for sensor in sensors:
		print "processing sensor {}".format(sensor)
		sensorData = filter(lambda x: x[1] == sensor, result)

		for label in labels:
			dates = [datetime.fromtimestamp(x[0]) for x in sensorData]
			xValues = md.date2num(dates)

			yValues = [x[label] for x in sensorData]
			axis[label].plot(xValues, yValues)
			axis[label].autoscale_view()


			
	T = sum([x[2] for x in result])/len(result)
	RH = sum([x[3] for x in result])/len(result)

	picture = savePlot("{}".format(result[0][0]))
	tweet = "Temperature: {:10.1f}, Humidity: {:10.1f}".format(T, RH)

	return (tweet, picture)


def createPlot():
	#[u'grayscale', u'bmh', u'dark_background', u'ggplot', u'fivethirtyeight']	
	plt.style.use("ggplot")
	fig, axis = plt.subplots(nrows=len(labels), sharex=True)				

	for ax in axis: 
		ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))

	axis = dict(zip(labels, axis))
	for a in axis: axis[a].set_title(labels[a])

	return axis

def savePlot(label):
	lc, lb = plt.xticks()
	plt.setp(lb, rotation=45)

	filename = "{}/{}.png".format(logDirectory, label)
	print "saving file " + filename
	plt.savefig(filename, dpi = 100)
	print "saved"

	matplotlib.pyplot.close("all")	
	return filename

def postTweet(tweet, picture):
	print tweet
	t = Twitter(auth=OAuth(token, token_key, con_secret, con_secret_key))

	with open(picture, "rb") as imagefile:
		params = {"media[]": imagefile.read(), "status": "Average data since last report\n{}".format(tweet)}
		t.statuses.update_with_media(**params)
	
	os.remove(picture)

while True:

	try:
		tweet = runReport()
		postTweet (*tweet)

	except:
		print sys.exc_info()

	time.sleep(refreshSec)

