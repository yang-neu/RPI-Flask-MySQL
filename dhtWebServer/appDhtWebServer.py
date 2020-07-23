#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  appDhtWebServer.py
#  
#  Created by MJRoBot.org 
#  10Jan18

'''
	RPi Web Server for DHT captured data  
'''

import pymysql.cursors

from flask import Flask, render_template, request
app = Flask(__name__)

# Retrieve data from database
def getData():
    try:
        conn = pymysql.connect(
            user='alex',
            passwd='!Passw0rd',
            host='192.168.11.48',
            db='temp_db'
        )
        curs=conn.cursor()

        curs.execute("SELECT * FROM dht11_sensor ORDER BY probe_date DESC LIMIT 1;")
        rows = curs.fetchall()
        print("Total number of rows in Laptop is: ", curs.rowcount)

        time = '2020-1-2'
        temp = '12'
        hum = '34'
        for row in rows:
            print('No:', row[0], 'Content:', row[1])
            time = str(row[1])
            temp = row[2]
            hum = row[3]
            print(time, temp, hum)
        conn.close()
        return time, temp, hum
    except pymysql.InternalError as e:
        print("Error reading data from MySQL table", e)
    finally:
        if (conn.open):
            curs.close()
            conn.close()
            print("MySQL connection is closed")

# main route 
@app.route("/")
def index():
	
    time, temp, hum = getData()
    print(time, temp, hum)
    templateData = {
      'time'	: time,
      'tempLab'	: temp,
      'humLab'	: hum
    }
    return render_template('index.html', **templateData)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=False)

