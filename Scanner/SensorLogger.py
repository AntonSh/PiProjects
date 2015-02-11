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

# Gracefull shutdown
def signal_handler(signal, frame):
        print('Caught signal, exiting')

        sys.exit(0)

sensorPins = [2, 17]
logFile = "../logs/control.log"
databaseFile = "../Data/sensor_stream.db"
refreshSec = 10

SensorReader.setup(sensorPins)

signal.signal(signal.SIGINT, signal_handler)


while True:
    try:
        con = lite.connect(databaseFile)

        value = SensorReader.getReadings() 
        timestamp = int(time.time())
        cur = con.cursor()  
        for data in value:
            row = (timestamp, data['pin'], data['temp'], data['humidity'])
            print row
            cur.execute("insert into sensor_log values(?,?,?,?)", row)
        
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

        time.sleep(refreshSec)
