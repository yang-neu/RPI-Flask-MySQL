#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  appDhtWebHist_v2.py
#  
#  Created by MJRoBot.org 
#  10Jan18

'''
	RPi WEb Server for DHT captured data with Gage and Graph plot  
'''

import pymysql.cursors
from datetime import datetime

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io

from flask import Flask, render_template, send_file, make_response, request
app = Flask(__name__)


# Retrieve LAST data from database
def getLastData():
    try:
        conn = pymysql.connect( user='alex', passwd='!Passw0rd', host='192.168.11.48', db='temp_db')
        curs=conn.cursor()
        curs.execute("SELECT * FROM dht11_sensor ORDER BY probe_date DESC LIMIT 1")
        row = curs.fetchone()
        time = str(row[1])
        temp = row[2]
        hum = row[3]
        return time, temp, hum
    except pymysql.InternalError as e:
          print("Error reading data from MySQL table", e)
    finally:
          if (conn.open):
              curs.close()
              conn.close()
              print("MySQL connection is closed")

# Get 'x' samples of historical data
def getHistData (numSamples):
    try:
        conn = pymysql.connect( user='alex', passwd='!Passw0rd', host='192.168.11.48', db='temp_db')
        curs=conn.cursor()
        sql = "SELECT * FROM dht11_sensor ORDER BY probe_date DESC LIMIT %s"
        print(sql, numSamples)
        curs.execute(sql,(numSamples,))
        data = curs.fetchall()
        dates = []
        temps = []
        hums = []
        for row in reversed(data):
                dates.append(str(row[1]))
                temps.append(row[2])
                hums.append(row[3])
                temps, hums = testeData(temps, hums)
        return dates, temps, hums
    except pymysql.InternalError as e:
          print("Error reading data from MySQL table", e)
    finally:
          if (conn.open):
              curs.close()
              conn.close()
              print("MySQL connection is closed")

def getHistDataL (numSamples):
    dates = []
    temps = []
    hums = []
    maxOnce = 300
    while True:
        mod = numSamples % maxOnce
        remain = numSamples - mod
        print ('remian' , remain)
        if (remain > 0):
            ds,ts,hs = getHistData (maxOnce)
            dates = dates + ds
            temps = temps + ts
            hums = hums + hs
            continue
        else:
            ds,ts,hs = getHistData (mod)
            dates = dates + ds
            temps = temps + ts
            hums = hums + hs
            break

    return dates, temps, hums

# Test data for cleanning possible "out of range" values
def testeData(temps, hums):
	n = len(temps)
	for i in range(0, n-1):
		if (temps[i] < -10 or temps[i] >50):
			temps[i] = temps[i-2]
		if (hums[i] < 0 or hums[i] >100):
			hums[i] = temps[i-2]
	return temps, hums


# Get Max number of rows (table size)
def maxRowsTable():
    try:
        conn = pymysql.connect( user='alex', passwd='!Passw0rd', host='192.168.11.48', db='temp_db')
        curs=conn.cursor()
        curs.execute("select COUNT(temp) from  dht11_sensor")
        (maxNumberRows,) = curs.fetchone()

        return maxNumberRows
    except pymysql.InternalError as e:
          print("Error reading data from MySQL table", e)
    finally:
          if (conn.open):
              curs.close()
              conn.close()
              print("MySQL connection is closed")

# Get sample frequency in minutes
def freqSample():
    times, temps, hums = getHistData (2)
    fmt = '%Y-%m-%d %H:%M:%S'
    tstamp0 = datetime.strptime(times[0], fmt)
    tstamp1 = datetime.strptime(times[1], fmt)
    freq = tstamp1-tstamp0
    freq = int(round(freq.total_seconds()/60))
    if (freq == 0):
        freq = 1
    return (freq)

# define and initialize global variables
global numSamples
numSamples = maxRowsTable()
if (numSamples > 101):
        numSamples = 100

global freqSamples
freqSamples = freqSample()

global rangeTime
rangeTime = 100
				
		
# main route 
@app.route("/")
def index():
	time, temp, hum = getLastData()
	templateData = {
	  'time'		: time,
      'temp'		: temp,
      'hum'			: hum,
      'freq'		: freqSamples,
      'rangeTime'		: rangeTime
	}
	return render_template('index.html', **templateData)


@app.route('/', methods=['POST'])
def my_form_post():
    global numSamples 
    global freqSamples
    global rangeTime
    rangeTime = int (request.form['rangeTime'])
    if (rangeTime < freqSamples):
        rangeTime = freqSamples + 1
    numSamples = rangeTime//freqSamples
    numMaxSamples = maxRowsTable()
    if (numSamples > numMaxSamples):
        numSamples = (numMaxSamples-1)
    
    time, temp, hum = getLastData()
    
    templateData = {
	  'time'		: time,
      'temp'		: temp,
      'hum'			: hum,
      'freq'		: freqSamples,
      'rangeTime'	: rangeTime
	}
    return render_template('index.html', **templateData)
	
	
@app.route('/plot/temp')
def plot_temp():
	times, temps, hums = getHistData(numSamples)
	ys = temps
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.set_title("Temperature [°C]")
	axis.set_xlabel("Samples")
	axis.grid(True)
	xs = range(numSamples)
	axis.plot(xs, ys)
	canvas = FigureCanvas(fig)
	output = io.BytesIO()
	canvas.print_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'
	return response

@app.route('/plot/hum')
def plot_hum():
	times, temps, hums = getHistData(numSamples)
	ys = hums
	fig = Figure()
	axis = fig.add_subplot(1, 1, 1)
	axis.set_title("Humidity [%]")
	axis.set_xlabel("Samples")
	axis.grid(True)
	xs = range(numSamples)
	axis.plot(xs, ys)
	canvas = FigureCanvas(fig)
	output = io.BytesIO()
	canvas.print_png(output)
	response = make_response(output.getvalue())
	response.mimetype = 'image/png'
	return response
	
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=False)

