# Author: MrEmsii
# Date: 05.08.2024
# https://github.com/MrEmsii

import sqlite3, shutil, datetime, traceback, os
import numpy as np
import pandas as pd
import threading

# from tabulate import tabulate
import matplotlib.pyplot as plt
import matplotlib.dates as dates

class Datas:
    def __init__(self, date=None, time=None, temp=None, temp_avr=None, temp_min=None, temp_max=None) -> None:
        self.date = date
        self.time = time
        self.temp = temp
        self.temp_avr = temp_avr
        self.temp_min = temp_min
        self.temp_max = temp_max

class thread:
    def Table_Maker_thread(placeBase, data, keyType, targetTable):
        t_calc = threading.Thread(target=operation.calculatio, args=(placeBase, data, keyType, targetTable,))
        t_calc.start()
        t_calc.join()

class operation:
    def calculatio(placeBase, data, keyType, targetTable):
        date_and_time =  dictionery.for_all(data, keyType)
        date_and_time =  calc.date_and_time(date_and_time)
        SQLbase.insert(placeBase, date_and_time, targetTable)

class dictionery:
    def for_all(base, keyType="date", target='temp_dot'):
        temperatures_by_date_hour = {}
        for _, row in base.iterrows():
            date = row['data']
            if keyType == "datetime":
                time = row['time']
                key = (date, time)
            elif keyType == "date":
                key = (date)
            temperature = row[target]
            if key not in temperatures_by_date_hour:
                temperatures_by_date_hour[key] = []
            temperatures_by_date_hour[key].append(temperature)
        return temperatures_by_date_hour

class calc:
    def averge(temperatures_by_date_hour):
        data = []
        for key, temps in temperatures_by_date_hour.items():
            date = key
            avg_temp = round(np.mean(temps), 2)
            data.append((date, avg_temp))
        data_array = np.array(data, dtype=[
            ('date', 'datetime64[D]'), 
            ('Average', 'float64')
            ])
        return data_array   

    def date_and_time(temperatures_by_date_hour):
        data = []
        for key, temps in temperatures_by_date_hour.items():
            avg_temp = round(np.mean(temps),2)
            min_temp = np.min(temps)
            max_temp = np.max(temps)
            try:
                date, hour = key
                data.append((date, hour + ":00:00", avg_temp, min_temp, max_temp))
                columns = [
                    ('date', 'U10'), 
                    ('hour + ":00:00"', 'U10'), 
                    ('avg_temp', 'float64'), 
                    ('min_temp', 'float64'), 
                    ('max_temp', 'float64')
                ]
            except:
                date = key
                data.append((date, avg_temp, min_temp, max_temp))
                columns = [
                    ('date', 'U10'), 
                    ('avg_temp', 'float64'), 
                    ('min_temp', 'float64'), 
                    ('max_temp', 'float64')
                ]        
        
        data_array = np.array(data, dtype=columns)
        return data_array

    def average_all(data):
        avrg_averge =   dictionery.for_all(data, target='TEMP_AVERAGE')
        avrg_min    =   dictionery.for_all(data, target='TEMP_MIN')
        avrg_max    =   dictionery.for_all(data, target='TEMP_MAX')

        avrg_averge =   calc.averge(avrg_averge)
        avrg_min    =   calc.averge(avrg_min)
        avrg_max    =   calc.averge(avrg_max)

        avrg_averge =   dict(avrg_averge)
        avrg_min    =   dict(avrg_min)
        avrg_max    =   dict(avrg_max)

        average_day =   pd.DataFrame(
            {
            'TEMP_day_AVERAGE': avrg_averge,
            'TEMP_day_MIN': avrg_min,
            "TEMP_day_MAX": avrg_max
            })

        average_day.reset_index(inplace=True)
        average_day.rename(columns={'index': 'Date'}, inplace=True)

        return average_day

class SQLbase:
    def create(place):
        connect = SQLbase.connect(place)

        cursor = connect.cursor()
        cursor.execute("DROP TABLE IF EXISTS Hours")
        cursor.execute("DROP TABLE IF EXISTS Days")
        cursor.execute("DROP TABLE IF EXISTS Average")
        connect.execute("""
            CREATE TABLE IF NOT EXISTS Hours (
                id INTEGER PRIMARY KEY ASC,
                data varchar(250) NOT NULL,
                time varchar(250) NOT NULL,
                TEMP_AVERAGE varchar(250) NOT NULL,
                TEMP_MIN varchar(250) NOT NULL,
                TEMP_MAX varchar(250) NOT NULL
            )""")

        connect.execute("""
            CREATE TABLE IF NOT EXISTS Days (
                id INTEGER PRIMARY KEY ASC,
                data varchar(250) NOT NULL,
                TEMP_AVERAGE varchar(250) NOT NULL,
                TEMP_MIN varchar(250) NOT NULL,
                TEMP_MAX varchar(250) NOT NULL
            )""")
        
        connect.execute("""
            CREATE TABLE IF NOT EXISTS Average (
                id INTEGER PRIMARY KEY ASC,
                data varchar(250) NOT NULL,
                TEMP_day_AVERAGE varchar(250) NOT NULL,
                TEMP_day_MIN varchar(250) NOT NULL,
                TEMP_day_MAX varchar(250) NOT NULL
            )""")
        
    def connect(place):
        return sqlite3.connect(place)

    def take_full(file):
        connect = SQLbase.connect(file)
        cursor = connect.cursor()
        cursor.execute("SELECT data, godzina, temp_dot FROM Temperatura")
        data = cursor.fetchall()
        column_name = np.array(data, dtype=[
            ('date', 'U10'), 
            ('time', 'U2'), 
            ('temperature', 'float64')
            ])
        base = pd.DataFrame(column_name, columns=['date', 'time', 'temperature'])
        connect.close()
        return base

    def take_Hours(file, table):
        connect = SQLbase.connect(file)
        cursor = connect.cursor()
        string = "SELECT * FROM " + table
        cursor.execute(string)
        data = cursor.fetchall()
        column_name = np.array(data, dtype=[
            ("id", "U10"), 
            ('date', 'U10'), 
            ('time', 'U2'), 
            ('temp_average', 'float64'), 
            ('temp_min', 'float64'), 
            ('temp_max', 'float64')
            ])
        base = pd.DataFrame(column_name, columns=['id', 'date', 'time', 'temp_average', 'temp_min', 'temp_max'])
        connect.close()
        return base

    def take(file, table):
        connect = SQLbase.connect(file)
        cursor = connect.cursor()
        string = "SELECT * FROM " + table
        cursor.execute(string)
        data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        column_name = SQLbase.columns_names_to_np(columns)
        column_name = np.array(data, dtype=column_name)
        base = pd.DataFrame(column_name, columns=columns)
        connect.close()
        
        return base
    
    def columns_names_to_np(columns):
        values_name = [("id", "U10"), ('data', 'U10')]
        # Początkowa tablica NumPy z krotkami
        # Sprawdzenie, czy "TIME" znajduje się w liście kolumn
        for value in columns[2:]:
            if value == 'temp_comma' or value == 'jednostka' or value == 'TIME' or value == 'time':
                values_name.append((value, 'U2'))
            else:
                values_name.append((value, 'float64'))
        return values_name

    def insert(place, data, where ):
        try:
            data = [
                (
                    timestamp.strftime('%Y-%m-%d') if isinstance(timestamp, pd.Timestamp) else timestamp,
                    temp_day_average,
                    temp_day_min,
                    temp_day_max
                )
                for timestamp, temp_day_average, temp_day_min, temp_day_max in data
            ]
        except:
            pass      
        count_data_to_insert = len(data[0])
        connect = SQLbase.connect(place)
        count_data_to_insert = count_data_to_insert * ",?"
        table = str("INSERT INTO " + where + " VALUES(NULL" + count_data_to_insert + ");")
        connect.executemany(table, data)
        connect.commit()
        connect.close()

class plots:
    def plot_trend(x_num, xd):
        return np.polyfit(x_num, xd, 1)

    def example_plot(data):
        with plt.style.context('ggplot'):
            print(plt.style.available)
            fig = plt.figure()
            fig.set_figheight(5)
            fig.set_figwidth(9)

            ax1 = plt.subplot2grid((31, 17), (0, 0), colspan=31, rowspan=11)
            ax3 = plt.subplot2grid((31, 17), (16, 0), colspan=8, rowspan=14)
            ax4 = plt.subplot2grid((31, 17), (16, 9), colspan=8, rowspan=14)       

            for index, ax in enumerate([ax1, ax3, ax4]):
                ax.plot(data['Date'], data.iloc[:,index+1], label = data.columns[index+1])
                ax.grid(True)
                ax.set_xlabel('Data', fontsize=8)
                ax.set_ylabel('Temp [*C]', fontsize=8)
                ax.set_title(data.columns[index+1], fontsize=8)
                ax.tick_params(axis='x', labelrotation = 45)

                plt.draw()
  
try:
    Heat = "C:\GitHUB\Temp_Room_Statistic\Heat.db"
    Stats2 = "C:\GitHUB\Temp_Room_Statistic\Stats2.db"

    SQLbase.create(Stats2)

    date1       =    datetime.datetime.now()
    
    data        =    SQLbase.take(Heat, "Temperatura")

#\/ NOT USED
    # Heat        =    Datas( 
    #     date=data['date'], 
    #     time=data['time'], 
    #     temp=data['temperature']
    #     ) 
#/\ NOT USED    

    thread.Table_Maker_thread(Stats2, data, "datetime", "Hours")
    thread.Table_Maker_thread(Stats2, data, "date", "Days")
    avrg           =   SQLbase.take(Stats2, "Hours", )
    average_day    =   calc.average_all(avrg)
    data_to_insert =   average_day.values.tolist()
    SQLbase.insert(Stats2, data_to_insert, "Average")
 
    date2          =   datetime.datetime.now()
    
    print(int((date2 - date1).seconds))

    # plots.example_plot(date_and_time)
    # plots.example_plot(date_data)
    plots.example_plot(average_day)
    plt.show()   
    
except KeyboardInterrupt:
    print("UPS!")   
