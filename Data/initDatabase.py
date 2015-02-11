#!/usr/bin/python
# create database and tables

import sqlite3 as lite

datafile = "sensor_stream.db"

con = lite.connect(datafile)
cur = con.cursor()

cur.execute("create table sensor_log(time_stamp date, sensor_id integer, temperature real, humidity real)")
con.close()

