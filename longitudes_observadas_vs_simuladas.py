import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import matplotlib.dates as mdates
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry
)
import pandas as pd
from datetime import datetime

#Fechas laboreo
fecha_laboreo_1 = pd.to_datetime("2023-11-27") 
fecha_laboreo_2 = pd.to_datetime("2024-11-21") 

#Obtener longitudes
# Cargar la capa (si no está ya cargada)
ruta = r"C:\Users\inigo.barberena\OneDrive - UPNA\Tesis\Pitillas\longitud volumen\longitudes.gpkg"
layer = QgsVectorLayer(ruta, "longitud", "ogr")

if not layer.isValid():
    print("Error al cargar la capa")
else:
    print("Capa cargada correctamente")

# Crear listas para guardar datos
fechas = []
longitudes = []
gullies = []

# Iterar sobre las features
for feature in layer.getFeatures():
    geom = feature.geometry()
    if geom is not None and geom.isGeosValid():
        longitud_m = feature["Length (m)"]
        fecha_str = feature["Date"]
        gully = feature["Gully ID"]
        
        # Convertir fecha al formato deseado: "día mes año"
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")  # ajusta este formato si es distinto
            fecha_formateada = fecha.strftime("%d %B %Y")
        except:
            fecha_formateada = fecha_str  # si falla, dejamos el original

        fechas.append(fecha_formateada)
        longitudes.append(round(longitud_m, 2))
        gullies.append(gully)

# Crear el DataFrame
df = pd.DataFrame({
    "Date": fechas,
    "Longitud_m": longitudes,
    "Gully":gullies
})

#Select gully
gully_id = 1
df = df[df["Gully"]==gully_id]


# Agrupar por la fecha y sumar la longitud
df_longitudes = df.groupby('Date', as_index=False)['Longitud_m'].sum()
df_longitudes['Date'] = pd.to_datetime(df_longitudes['Date'], dayfirst=True)
#poner las fechas de laboreo que no hay cárcavas
df_longitudes = pd.concat([df_longitudes,pd.DataFrame([{"Date": fecha_laboreo_1, "Longitud_m": 0}])])
df_longitudes = pd.concat([df_longitudes,pd.DataFrame([{"Date": fecha_laboreo_2, "Longitud_m": 0}])])
df_longitudes = df_longitudes.sort_values(by='Date')
#Añadir el volumen
conversion_longitud_volumen = 2
df_longitudes["Volumen"] = df_longitudes["Longitud_m"]*conversion_longitud_volumen

#Poner valores cada día
df_longitudes = df_longitudes.set_index('Date')

# Crear un índice diario desde la fecha mínima a la máxima
fecha_diaria = pd.date_range(start=df_longitudes.index.min(), end=df_longitudes.index.max(), freq='D')

# Reindexar al índice diario y rellenar con el valor anterior
df_diario = df_longitudes.reindex(fecha_diaria).ffill()

# Opcional: renombrar el índice a 'Date' y resetearlo
df_diario.index.name = 'Date'
df_diario = df_diario.reset_index()


#Obtener longitudes simuladas
ruta_csv = r"C:\Users\inigo.barberena\OneDrive - UPNA\Tesis\Pitillas\longitud volumen\simulated_lengths.csv"

# Leer CSV ignorando las dos primeras filas
simulated_lengths = pd.read_csv(ruta_csv)
simulated_lengths['Date'] = pd.to_datetime(simulated_lengths['Date'], format="%Y-%m-%d")
#poner las fechas de laboreo que no hay cárcavas
simulated_lengths = pd.concat([simulated_lengths,pd.DataFrame([{"Date": fecha_laboreo_1, "Length of gullies": 0}])])
simulated_lengths = pd.concat([simulated_lengths,pd.DataFrame([{"Date": fecha_laboreo_2, "Length of gullies": 0}])])
simulated_lengths = simulated_lengths.sort_values(by='Date')
#Filtrar datos desde el inicio del primer laboreo
simulated_lengths = simulated_lengths[simulated_lengths['Date'] >= fecha_laboreo_1]

#Poner datos diarios
simulated_lengths = simulated_lengths.set_index('Date')
# Crear un índice diario desde la fecha mínima a la máxima
fecha_diaria = pd.date_range(start=simulated_lengths.index.min(), end=simulated_lengths.index.max(), freq='D')

# Reindexar al índice diario y rellenar con el valor anterior

#si hay fechas duplicadas me quedo con el primer valor 
simulated_lengths = simulated_lengths.loc[~simulated_lengths.index.duplicated(keep='first')] 
simulated_lengths = simulated_lengths.reindex(fecha_diaria).ffill()

s = simulated_lengths["Length of gullies"]
simulated_lengths["Length of gullies"] = s.groupby((s == 0).cumsum()).cummax()


#Obtener valores precipitacion y humedad
# Ruta al archivo
ruta_csv = r"C:\Users\inigo.barberena\OneDrive - UPNA\Tesis\Pitillas\longitud volumen\Medidas de las sondas.csv" # cámbialo por la ruta real

# Leer CSV ignorando las dos primeras filas
df = pd.read_csv(ruta_csv, skiprows=2, sep=';', encoding='utf-8',usecols=[0,1, 6, 10,14])



# Renombrar columnas si quieres
df.columns = ["Fecha", 'Precipitacion', '10 cm',"20 cm","30 cm"]

# Reemplazar comas por puntos y convertir a float
for col in df.columns[1:]:
    df[col] = df[col].astype(str).str.replace(',', '.')
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 1. Convertir la columna "Fecha" a formato datetime
df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y %H:%M:%S')
# 2. Calcular el promedio de '10 cm', '20 cm', '30 cm' por cada fecha
df['Promedio'] = df[['10 cm', '20 cm', '30 cm']].mean(axis=1)

# 3. Agrupar por semana
df['Semana'] = df['Fecha'].dt.to_period('D')  # Agrupar por semana (periodo semanal)

# 4. Sumar 'Precipitacion' por semana y calcular el promedio semanal de '10 cm', '20 cm', '30 cm'
df_semanal = df.groupby('Semana').agg({
    'Precipitacion': 'sum',  # Sumar precipitacion
    'Promedio': 'mean',  # Promedio de las tres columnas '10 cm', '20 cm', '30 cm'
    "10 cm":'mean',
    "20 cm":'mean',
}).reset_index()
df_semanal["Fecha"] = df_semanal["Semana"].apply(lambda x: x.start_time)


#Limitar las fechas de valores simulados
fecha_limite = pd.to_datetime("2025-04-11")
simulated_lengths = simulated_lengths[simulated_lengths.index <= fecha_limite]

#Obtener gráfico 
sns.set(style="whitegrid", palette="pastel")
# Crear la figura
# Crear la figura
fig, ax1 = plt.subplots(figsize=(14, 7))
ax2 = ax1.twinx()
ax3 = ax1.twinx()

ax1.set_zorder(ax3.get_zorder() + 1)  # o simplemente un valor alto como 10
ax1.patch.set_visible(False)

# Colores
color_lineas = 'black'
color_barras_precipitacion = '#1f77b4'
color_barras_humedad_10_cm = 'red'
color_barras_humedad_20_cm = 'orange'

# Título
ax1.set_title(f"Evolution of the length of gullies in northern system", fontsize=16, weight='bold')

# Eje derecho 1: Precipitación (barras invertidas)

ax2.bar(df_semanal["Fecha"], df_semanal['Precipitacion'].values, zorder = 2, color=color_barras_precipitacion, alpha=0.3, width=1, label='Precipitation')
ax2.set_ylabel("Precipitation (mm)", color='black', fontsize=12)
ax2.tick_params(axis='y', labelcolor='black')
#Set y lim
ax2.set_ylim(0, ax2.get_ylim()[1]*1.5)
ax2.invert_yaxis()
ax2.grid(False)

# Eje derecho 2: Humedad (barras normales)

ax3.spines["right"].set_position(("axes", 1.1))
ax3.bar(df_semanal["Fecha"], df_semanal['10 cm'].values/2, zorder = 1, alpha=0.4, width=1, label='Soil moisture 10 cm',color = color_barras_humedad_10_cm)
ax3.bar(df_semanal['Fecha'], df_semanal['20 cm'].values/2, bottom=df_semanal['10 cm'].values/2,  width=1, label='Soil moisture 20 cm',color = color_barras_humedad_20_cm)
ax3.set_ylabel("Soil moisture in first 20 cm (%)", color='black', fontsize=12)
ax3.tick_params(axis='y', labelcolor='black')
#Set y lim
ax3.set_ylim(0, ax3.get_ylim()[1]*1.5)
ax3.grid(False)

#Length
#ax1.plot(df_diario['Date'].values, df_diario['Longitud_m'].values, zorder = 3, color=color_lineas, linewidth=2, label='Observed gully lengths')
ax1.scatter(df_longitudes.index, df_longitudes['Longitud_m'].values, s = 20,zorder = 3, color="blue", marker='o', linewidth=2, label = "Observed gully lengths")
ax1.plot(simulated_lengths.index.values, simulated_lengths['Length of gullies'].values, zorder = 3, color=color_lineas, linewidth=2, label='Simulated gully lengths')
#Set y lim
ax1.set_ylim(ax1.get_ylim()[0], ax1.get_ylim()[1]*1.5)
# Eje izquierdo: longitud y volumen
ax1.set_ylabel("Length (m)", color=color_lineas, fontsize=12)
ax1.set_xlabel("Date", fontsize=12)


#Fecha laboreo
ax1.axvline(x=fecha_laboreo_1, color='red', linestyle='--', linewidth=1.5,alpha = 1)
ax1.axvline(x=fecha_laboreo_2, color='red', linestyle='--', linewidth=1.5,alpha = 1)

# Fechas bonitas
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b-%Y'))
fig.autofmt_xdate()

# Fondo blanco, cuadrícula
fig.patch.set_facecolor('white')
ax1.grid(True, linestyle='--', alpha=0.4)

# Reunir leyendas de todos los ejes
handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
handles3, labels3 = ax3.get_legend_handles_labels()


# Combinar todos
all_handles = handles1  + handles2 + handles3 
all_labels = labels1 + labels2 + labels3 

# Crear una leyenda combinada
ax1.legend(all_handles, all_labels, loc='best', frameon=True)

#X ticks
ax1.xaxis.set_major_locator(mdates.YearLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

# Ticks menores: cada mes
ax1.xaxis.set_minor_locator(mdates.MonthLocator())
ax1.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))

# Mostrar ambos
ax1.tick_params(axis='x', which='major', labelsize=10, pad=10)
ax1.tick_params(axis='x', which='minor', labelsize=8, rotation=0)

#Poner texto laboreo
ax1.text(pd.to_datetime("2023-12-10"), ax1.get_ylim()[1]*0.85, 'Tillage', color='red',
             ha='center', va='center', fontsize=10, fontweight='bold')
ax1.text(pd.to_datetime("2024-12-5"), ax1.get_ylim()[1]*0.85, 'Tillage', color='red',
             ha='center', va='center', fontsize=10, fontweight='bold')

plt.tight_layout()
#Guardar gráfico
plt.savefig(r"C:\Users\inigo.barberena\OneDrive - UPNA\Tesis\Pitillas\longitud volumen\observed_vs_simulated_lengths2.png",transparent=False,bbox_inches = "tight",dpi=600)


