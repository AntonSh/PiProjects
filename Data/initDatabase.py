#!/usr/bin/python
# create database and tables

import sqlite3 as lite

datafile = "sensor_stream.db"
contolFile = "contol_steam.db"

con = lite.connect(datafile)
cur = con.cursor()

cur.execute("create table sensor_log(time_stamp date, sensor_id integer, temperature real, humidity real)")
con.close()

con = lite.connect(contolFile)
cur = con.cursor()

cur.execute("create table control_log(time_stamp date, control_name text, value integer)")
con.close()
