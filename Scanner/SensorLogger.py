#!/usr/bin/python
import subprocess
import time
import sys
import signal 
from datetime import datetime, date
import argparse
import sqlite3 as lite
import os
import os.path
import GPIOControl
import SensorReader
import Utils

# Constants
logFile = "../logs/control.log"
databaseFile = "../Data/sensor_stream.db"

# Gracefull shutdown
def signal_handler(signal, frame):
        print('Caught signal, exiting')

        sys.exit(0)

def ps(pid):
    return subprocess.check_output(["/bin/ps", "hc", pid])

def handle_locked_gpio():
    try:
        print "Handling exec error"
        lockFile = "/var/run/pigpio.pid"

        if not os.path.isfile(lockFile):
            return

        pid = None
        with open(lockFile) as f:
            pid = f.readline().rstrip()

        if pid == None :
            return

        print "GPIO was locked by {}".format(pid)

        if os.path.exists("/proc/{}".format(pid)) :
            print "GPIO is legitimely locked by {}".format(ps(pid))
            return

        print "Process {} is not running, removing lock file".format(pid)
        os.remove("/var/run/pigpio.pid")

    except:
        type, value, tb = sys.exc_info()
        print ("Failed to handle exec error", type, value.cmd, value.output)



parser = argparse.ArgumentParser(description='Polls environment sensors and stores data in Sqlite database')
parser.add_argument('-pins', type=int, nargs='+', help='List of GPIO port numbers on which sensors connected', required = True)
parser.add_argument('-refreshSec', type=int, help='Delays between sensor polling, sec', default=10)

args = parser.parse_known_args()[0]

sensorPins = args.pins
refreshSec = args.refreshSec

print "Running sensor logging on pins {} refresh delay {} sec.".format(sensorPins, refreshSec)

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
        type, value, tb = sys.exc_info()
        if isinstance(value, subprocess.CalledProcessError):
            if "readtemp" in value.cmd[0] and value.returncode == 1:
                handle_locked_gpio()
                continue

        print (type, value, tb)

    finally:
        if con:
            con.close() 

        time.sleep(refreshSec)
