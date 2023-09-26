

#Esto es para el resultado espacial con las celdas

import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

cell = "All cells"
date_in = "1/1/1998"
date_fin = "31/12/2001"
#Se obtienen los datos ordenados
path = r"D:\SPAIN_Pitillas_Cobaza1\INPUTS\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
def df_section(fichero,delete_second =False):
   file = open(fichero)
   csvreader = csv.reader(file)
   rows = []
   for row in csvreader:
           rows.append(row)
   lista = []
   a = 0
   for i in rows:
       try:
           if i[0]=="Gregorian":
               a = 1
               lista.append(i)
           elif a ==1:
               lista.append(i[:-1])
       except:
           continue
   if delete_second:
       lista.pop(1)
   return pd.DataFrame(columns = lista[0],data = lista[1:])

df_raw = df_section(path,delete_second=True).iloc[2:,]
df = pd.DataFrame(data = {"Year":[int(x) for x in df_raw["Year"]],"Month":[int(x) for x in df_raw["Month"]],"Day":[int(x) for x in df_raw["Day"]],"Cell":[int(x) for x in df_raw["ID"]],"Runoff":[float(x) for x in df_raw["Depth"]],"RSS":[float(df_raw["Rainfall"].iloc[x]) +float(df_raw["Snowfall"].iloc[x])+float(df_raw["Snowmelt"].iloc[x]) for x in range(len(df_raw))]})
df['Fecha'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
#Se pone la estación
def estacion(fecha):
    estaciones = {
        1: (datetime(year=fecha.year, month=3, day=21), datetime(year=fecha.year, month=6, day=21)),
        2: (datetime(year=fecha.year, month=6, day=21), datetime(year=fecha.year, month=9, day=21)),
        3: (datetime(year=fecha.year, month=9, day=21), datetime(year=fecha.year, month=12, day=21))
    }
    for estacion, (inicio,fin) in estaciones.items():
        if inicio<= fecha < fin:
            return estacion
    return 4
df["Season"] = [estacion(x) for x in df.Fecha]
#Aquí se filtran por celda
if cell != "All cells":
    df = df[df.Cell==cell]
#Aquí se filtra por fecha
date_in = datetime(int(date_in.split("/")[2]),int(date_in.split("/")[1]),int(date_in.split("/")[0]))
date_fin = datetime(int(date_fin.split("/")[2]),int(date_fin.split("/")[1]),int(date_fin.split("/")[0]))
df = df[(df.Fecha>=date_in)&(df.Fecha<=date_fin)]

#Creación del dataframe final
cells = np.unique(df.Cell)
#Se añaden meses
dic_month = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
resultado_final = pd.DataFrame()
for i in cells:
    df_month = df[df.Cell==i]
    df_month = df_month.groupby('Fecha').mean(numeric_only=True)[["Runoff"]]
    df_month = df_month.resample('M').sum()
    df_month = df_month.groupby(df_month.index.month).sum()
    resultado_concat = pd.DataFrame()
    for m in df_month.index:
        resultado_concat[dic_month[m]]=[df_month[df_month.index == m]["Runoff"].iloc[0]]
    resultado_final = pd.concat([resultado_final, resultado_concat])
resultado_final.index = cells

#Se añaden años
resultado = pd.DataFrame()
for i in cells:
    df_year = df[df.Cell==i]
    df_year = df_year.groupby('Fecha').mean(numeric_only=True)[["Runoff"]]
    df_year = df_year.resample("Y").sum()
    df_year = df_year.groupby(df_year.index.year).sum()
    resultado_concat = pd.DataFrame()
    for m in df_year.index:
        resultado_concat[m]=[df_year[df_year.index == m]["Runoff"].iloc[0]]
    resultado = pd.concat([resultado, resultado_concat])
resultado.index = cells
year_average = [(x,resultado[x].sum()/len(resultado)) for x in resultado.columns]
resultado_final = pd.concat([resultado_final, resultado], axis=1)

#Se añaden las estaciones
dic_season = {1:"Spring",2:"Summer",3:"Autumn",4:"Winter"}
resultado = pd.DataFrame()
for i in cells:
    df_season = df[df.Cell==i]
    df_season = df_season.groupby(df_season.Season).sum(numeric_only=True)["Runoff"]
    resultado_concat = pd.DataFrame()
    for m in df_season.index:
        resultado_concat[dic_season[m]]=[df_season[df_season.index == m].iloc[0]]
    resultado = pd.concat([resultado, resultado_concat])
resultado.index = cells
resultado_final = pd.concat([resultado_final, resultado], axis=1)

#Se añade la columna del total
resultado_final.insert(0, 'Total', [df[df.Cell==x]["Runoff"].sum() for x in cells])


