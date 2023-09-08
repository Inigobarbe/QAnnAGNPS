import pandas as pd
import numpy as np
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#ESCORRENTÍA
cell = ""
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
if type(cell) ==int:
    df = df[df.Cell==cell]

#SE CREA DE EVOLUCIÓN GRÁFICO
#Se crean los dataframes dependiendo de si se ha filtrado la celda
if type(cell) != int:
    df_graph = df.groupby('Fecha').mean()[["Runoff","RSS"]]
else:
    df_graph = df
acumulado_runoff = df_graph['Runoff'].cumsum()
#Se empieza con el gráfico
#Se crean los ejes
plt.rcParams["figure.figsize"] = [10, 8]
fig = plt.figure()
ax0 = plt.subplot()
ax1 = ax0.twinx()
ax2 = ax0.twinx()
#Se crean los dibujos
ax0.bar(df_graph.index, df_graph['Runoff'], width =6 ,color='tab:blue', alpha=1, label='Runoff')
ax1.bar(df_graph.index, df_graph['RSS'], width =6 ,color='tab:red', alpha=0.8, label='Rainfall + Snowfall + Snowmelt')
ax2.plot(df_graph.index, acumulado_runoff ,color="green", linestyle='--', label='Accumulated runoff')
#Labels de los ejes
ax0.set_xlabel("Date",size = 15,family="arial",weight = "bold",color = "black")
ax0.set_ylabel("Runoff (mm)",size = 15,family="arial",weight = "bold",color = "black")
ax1.set_ylabel("Rainfall + Snowfall + Snowmelt (mm)",size = 15,family="arial",weight = "bold",color = "black")
ax2.set_ylabel("Accumulated runoff (mm)",size = 15,family="arial",weight = "bold",color = "black")
#Cambiar límites de los ejes
ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.85)
ax1.set_ylim(ax1.get_ylim()[0],ax1.get_ylim()[1]*1.85)
ax2.set_ylim(ax2.get_ylim()[0],ax2.get_ylim()[1]*1.75)
#Fuente del eje
ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
ax1.tick_params(axis = "both",colors = "black",labelsize = 11)
ax2.tick_params(axis = "both",colors = "black",labelsize = 11)
#Mover eje a la derecha
ax2.spines['right'].set_position(('outward', 80))
ax2.spines["right"].set_color("black")
#Invertir eje
ax1.invert_yaxis()
# Agregar una etiqueta en el último punto del acumulado
ultimo_valor_acumulado = acumulado_runoff.iloc[-1]
ax2.annotate(f'{ultimo_valor_acumulado:.2f} mm',
             xy=(df_graph.index[-1], ultimo_valor_acumulado),
             xytext=(-50, 10), textcoords='offset points',
             fontsize=11, color='black', weight='bold')
#Formato eje x
ax0.xaxis.set_major_locator(mdates.YearLocator(base=1, month=1, day=1))
ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax0.xaxis.set_minor_locator(mdates.MonthLocator())
#Leyenda
legend = fig.legend(bbox_to_anchor=(0.11,0.57,0.3,0.3),framealpha=0.7)
legend.legendPatch.set_edgecolor("black")
legend.legendPatch.set_facecolor("white")
legend.legendPatch.set_linewidth(1)
#Guardar gráfico
plt.savefig(r"D:\Evolucion.png",transparent=False,bbox_inches = "tight",dpi=300)

#GRÁFICO DE TOP 10
#Se calculan los datos
n_top_values = 10
top_runoff = df_graph['Runoff'].nlargest(n_top_values) 
top_runoff_dates = df_graph.index[df_graph['Runoff'].isin(top_runoff)]

table_data = {'Fecha': top_runoff_dates, 'Runoff (mm)': round(top_runoff,2)}
table_df = pd.DataFrame(table_data)

plt.rcParams["figure.figsize"] = [10, 8]
fig, ax = plt.subplots()

# Ajustar el formato de las fechas en el DataFrame
table_df['Fecha'] = table_df['Fecha'].dt.strftime('%Y-%m-%d')

table = ax.table(cellText=table_df.values, colLabels=table_df.columns, loc='center', cellLoc='center', colColours=['#f5f5f5'] * len(table_df.columns))

table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1, 1.5)

# Ocultar ejes x e y
ax.axis('off')

plt.show()
