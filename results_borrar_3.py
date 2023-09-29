
#Erosion
import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import itertools

#ESTO SE HACE INDEPENDIENTEMENTE DE LA ELECCIÓN
cell = "31"
date_in = "1/1/1998"
date_fin = "31/12/2001"
date_in = datetime(int(date_in.split("/")[2]),int(date_in.split("/")[1]),int(date_in.split("/")[0]))
date_fin = datetime(int(date_fin.split("/")[2]),int(date_fin.split("/")[1]),int(date_fin.split("/")[0]))

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
           if i[0]=="Month":
               a = 1
               lista.append(i)
           elif a ==1:
               lista.append(i[:-1])
       except:
           continue
   if delete_second:
       lista.pop(1)
   return pd.DataFrame(columns = lista[0],data = lista[1:])



def dataframe_creation(path,subtotal_column, erosion = False, source = None):

    df_raw = df_section(path,delete_second=False)
    if erosion:
        df = pd.DataFrame(data = {"Year":[int(x) for x in df_raw["Year"]],"Month":[int(x) for x in df_raw["Month"]],"Day":[int(x) for x in df_raw["Day"]],"Cell":[str(x) for x in df_raw["Cell ID"]],"Source":[str(x) for x in df_raw["Source"]],"Yield":[float(x) for x in df_raw["Subtotals [Mg]"]]})
    else:
        df = pd.DataFrame(data = {"Year":[int(x) for x in df_raw["Year"]],"Month":[int(x) for x in df_raw["Month"]],"Day":[int(x) for x in df_raw["Day"]],"Cell":[str(x) for x in df_raw["Cell ID"]],"Yield":[float(x) for x in df_raw[subtotal_column]]})
    #Se quitan las filas que no tengan un Cell ID como "Landscape" o "Watershed"
    lista = []
    for i in df.Cell:
        try:
            int(i)
            lista.append(1)
        except:
            lista.append(0)
    df["filtro"]=lista
    df = df[df.filtro==1].iloc[:,:-1]
    df["Cell"] = [int(x) for x in df.Cell]
    #Se filtra por tipo de origen
    if erosion:      
        df = df[df.Source == source]
    #Aquí se filtran por celda
    if type(cell) ==str:
        df = df[df.Cell==int(cell)]
    #Se pone la fecha
    df = df.assign(Fecha=pd.to_datetime(df[['Year', 'Month', 'Day']]))
    df = df.groupby('Fecha').sum(numeric_only=True).reset_index()
    df.set_index('Fecha', inplace=True)
    df = df["Yield"]
    rango_fechas_deseado = pd.date_range(start=date_in, end=date_fin, freq='D')
    df = df.reindex(rango_fechas_deseado, fill_value=0)
    return df

erosion = dataframe_creation(r"D:\SPAIN_Pitillas_Cobaza1\INPUTS\AnnAGNPS_EV_Sediment_yield_(mass).csv","Subtotals [Mg]",erosion = True,source = "Gully")
nitrogen = dataframe_creation(r"D:\SPAIN_Pitillas_Cobaza1\INPUTS\AnnAGNPS_EV_Nitrogen_yield_(mass).csv","Subtotal N [kg]")
carbon = dataframe_creation(r"D:\SPAIN_Pitillas_Cobaza1\INPUTS\AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv","Subtotal C [kg]")
phosphorus = dataframe_creation(r"D:\SPAIN_Pitillas_Cobaza1\INPUTS\AnnAGNPS_EV_Phosphorus_yield_(mass).csv","Subtotal P [kg]")

path = r"D:\SPAIN_Pitillas_Cobaza1\INPUTS\AnnAGNPS_EV_Sediment_yield_(mass).csv"
df_raw = df_section(path,delete_second=False)
df = pd.DataFrame(data = {"Year":[int(x) for x in df_raw["Year"]],"Month":[int(x) for x in df_raw["Month"]],"Day":[int(x) for x in df_raw["Day"]],"Cell":[str(x) for x in df_raw["Cell ID"]],"Source":[str(x) for x in df_raw["Source"]],"Yield":[float(x) for x in df_raw["Subtotals [Mg]"]]})
#Se quitan las filas que no tengan un Cell ID como "Landscape" o "Watershed"
lista = []
for i in df.Cell:
    try:
        int(i)
        lista.append(1)
    except:
        lista.append(0)
df["filtro"]=lista
df = df[df.filtro==1].iloc[:,:-1]
df["Cell"] = [int(x) for x in df.Cell]
#Se filtra por tipo de origen
df = df[df.Source == "Gully"]
#Se pone bien todo el tema de las fechas
df = df.assign(Fecha=pd.to_datetime(df[['Year', 'Month', 'Day']]))
number_cells = len(np.unique(df.Cell))
rango_fechas = pd.date_range(start=date_in, end=date_fin)
indice_repetido = np.repeat(rango_fechas, number_cells)
df_n = pd.DataFrame(index=indice_repetido)
cells = np.tile(np.unique(df.Cell), len(rango_fechas))
df_n["Cell"]= cells
df_n["Fecha"] = df_n.index
fechas_diarias = pd.date_range(start=df_n['Fecha'].min(), end=df_n['Fecha'].max(), freq='D')
df_resultado = pd.DataFrame({'Fecha': fechas_diarias})
tipos_de_celda = np.unique(df.Cell)
combinaciones = list(itertools.product(fechas_diarias, tipos_de_celda))
df_combinaciones = pd.DataFrame(combinaciones, columns=['Fecha', 'Cell'])
df_resultado = df_combinaciones.merge(df, on=['Fecha', 'Cell'], how='left')
df_resultado['Yield'].fillna(0, inplace=True)
df_resultado["Cell"]=np.tile(np.unique(df.Cell), len(rango_fechas))
df = df_resultado[["Cell","Fecha","Yield"]]
df.set_index('Fecha', inplace=True)


