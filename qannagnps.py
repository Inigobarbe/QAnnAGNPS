# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QAnnAGNPS
                              -------------------
        begin                : 2023-02-09
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Iñigo Barberena
        email                : inigo.barberena@unavarra.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

    
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from PyQt5.QtWidgets import QFrame
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject
from PyQt5.QtCore import QVariant,QObject, QThread, pyqtSignal, QSize
from qgis.PyQt import QtWidgets
from qgis.utils import iface
from qgis.core import *
from qgis.gui import QgsMapToolEmitPoint,QgsMessageBar
from PyQt5.QtGui import QFont,QColor
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QProgressBar, QLabel, QWidget, QHBoxLayout, QVBoxLayout
from qgis.core import QgsTask, QgsApplication
from PyQt5.QtGui import QPixmap



import subprocess
import os
import numpy as np
import pandas as pd
import math
from datetime import datetime
import shutil
from os import path, remove
import time
from osgeo import gdal, gdalconst
import math
import processing
import csv
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import statistics
from functools import partial
import itertools
from matplotlib.ticker import FuncFormatter

#Dialog files
from .ui.inputs_dialog import InputsDialog
from .ui.mapDialog import MapDialog
from .ui.coordinate_dialog import Coordinate
from .ui.coordinate_capture_dockwidget import CoordinateCaptureDockWidget

from .ui.control_pothole_dialog import ControlPotholeDialog
from .ui.control_peg_dialog import ControlPegDialog
from .ui.control_general_dialog import ControlGeneralDialog
from .ui.control_concepts_dialog import ControlConceptsDialog
from .ui.control_agwet_dialog import ControlAgwetDialog
from .ui.control_agbuf_dialog import ControlAgbufDialog
from .ui.control_topagnps_dialog import ControlTOPAGNPSDialog
from .ui.control_rasfor_dialog import ControlRasforDialog
from .ui.control_raspro_dialog import ControlRasproDialog
from .ui.dednm_dialog import DEDNMDialog
from .ui.agflow_dialog import AgflowDialog
from .ui.overwrite_dialog import OverwriteDialog
from .ui.output_dialog import OutputDialog
from .ui.existing_dialog import ExistingDialog
from .ui.documentation_dialog import DocumentationDialog

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .ui.ephemeral_gully_dialog import EphemeralGullyDialog
import os.path
import webbrowser
#from .Coordinate_capturer import PrintClickedPoint



class qannagnps():

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QAnnAGNPS_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QAnnAGNPS')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        
        #Inicializar variables
        self.first_start = None
        self.plugin_directory = os.getcwd()

    def tr(self, message):
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('EphemeralGully', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        '''Esto se ejecuta cuando se actualiza el complemento. Me imagino que también en más ocasiones'''
        #Crear variables para hacer referencia a los distintos dialogos
        self.dlg  = EphemeralGullyDialog()
        self.inputs = InputsDialog()
        self.cgeneral = ControlGeneralDialog()
        self.ctopagnps = ControlTOPAGNPSDialog()
        self.cpeg = ControlPegDialog()
        self.cagbuf = ControlAgbufDialog()
        self.cagwet = ControlAgwetDialog()
        self.cconcepts = ControlConceptsDialog()
        self.cpothole = ControlPotholeDialog()
        self.crasfor = ControlRasforDialog()
        self.craspro = ControlRasproDialog()
        self.dednm = DEDNMDialog()
        self.agflow = AgflowDialog()
        self.dlgmap = MapDialog()
        self.overwrite = OverwriteDialog()
        self.output = OutputDialog()
        self.existing = ExistingDialog()
        self.documentation = DocumentationDialog()
        
        #Boton principal
        icon_path = ':/plugins/qannagnps/images/logo.svg'
        icon_size = QSize(100, 100)

        icon = QIcon(icon_path)
        pixmap = icon.pixmap(icon_size)  # Escala el icono al tamaño deseado

        self.add_action(
            QIcon(pixmap),  # Aquí usamos la QPixmap escalada
            text=self.tr(u'Simulate'),
            callback=self.run,
    parent=self.iface.mainWindow())
       
        #Boton para mostrar outputs
        icon_path = ':/plugins/qannagnps/images/outputs.svg'
        self.add_action(icon_path,text=self.tr(u'Outputs'),callback=self.outputs,parent=self.iface.mainWindow())
        
        # will be set False in run()
        #self.first_start = True
        #Se pone el nombre de los diálogos
        self.dlg.setWindowTitle("QAnnAGNPS Simulation")
        self.output.setWindowTitle("QAnnAGNPS Data Visualization") 
        #Poner el nombre de las columnas al elegir la capa de suelos y usos
        self.dlg.cbSoil.currentIndexChanged.connect(self.cambios_suelo)
        self.dlg.cbMan.currentIndexChanged.connect(self.cambios_manejo)
        #Para que aparezcan las interfaces donde se pone el nombre de los inputs
        self.dlg.pb_ann.clicked.connect(self.inputs.show)
        #Al seleccionar el MDT que se establezca ya el directorio
        self.dlg.comboBox.currentIndexChanged.connect(self.setDirectory)
        #Conectar a los dialogos para los control files
        self.dlg.pbControl.clicked.connect(self.cgeneral.show)
        self.cgeneral.pushButton.clicked.connect(self.ctopagnps.show)
        self.cgeneral.pushButton_2.clicked.connect(self.cpeg.show)
        self.cgeneral.pushButton_3.clicked.connect(self.cagbuf.show)
        self.cgeneral.pushButton_4.clicked.connect(self.cagwet.show)
        self.cgeneral.pushButton_5.clicked.connect(self.cconcepts.show)
        self.cgeneral.pushButton_6.clicked.connect(self.cpothole.show)
        self.cgeneral.pushButton_8.clicked.connect(self.crasfor.show)
        self.cgeneral.pushButton_7.clicked.connect(self.craspro.show)
        self.cgeneral.pushButton_10.clicked.connect(self.dednm.show)
        self.cgeneral.pushButton_9.clicked.connect(self.agflow.show)
        #Para cerrar el diálogo cuando se le de a cancel
        self.dlg.pushButton_7.clicked.connect(self.dlg.close)
        self.dlg.pushButton_5.clicked.connect(self.dlg.close)
        #Asignar los valores de los control files a los diálogos
        self.dlg.pbControl.clicked.connect(self.asignar_valores_control_dialogo)
        #Añadir los valores del diálogo a los control files
        self.ctopagnps.pushButton.clicked.connect(self.create_control_file_topagnps)
        self.cpeg.pushButton.clicked.connect(self.create_control_file_peg)
        self.cagbuf.pushButton.clicked.connect(self.create_control_file_agbuf)
        self.cagwet.pushButton.clicked.connect(self.create_control_file_agwet)
        self.cconcepts.pushButton.clicked.connect(self.create_control_file_concepts)
        self.cpothole.pushButton.clicked.connect(self.create_control_file_pothole)
        self.crasfor.pushButton.clicked.connect(self.create_control_file_rasfor)
        self.craspro.pushButton.clicked.connect(self.create_control_file_raspro)
        self.dednm.pushButton.clicked.connect(self.create_control_file_dednm)
        self.agflow.pushButton.clicked.connect(self.create_control_file_agflow)
        
        #Cambiar el nombre en el control file de AGBUF.csv de las columnas Buffer y Vegetation al seleccionar una capa
        self.dlg.comboBox_2.currentIndexChanged.connect(self.buffer_nombre)
        self.dlg.comboBox_3.currentIndexChanged.connect(self.vegetation_nombre)
                        
        #Cambiar los colores de los inputs de AnnAGNPS según se hayan elegido o no. También se crean los archivos si es que no estaban creados. 
        #Primero se crean los diccionarios que relacionan el boton de abrir o crear documento con las líneas de texto
        dic_buttons_watershed = {self.inputs.w22:self.inputs.l_2,self.inputs.w23:self.inputs.l_3,self.inputs.w24:self.inputs.l_4,self.inputs.w25:self.inputs.l_5,self.inputs.w26:self.inputs.l_6,self.inputs.w27:self.inputs.l_7,self.inputs.w28:self.inputs.l_8,self.inputs.w29:self.inputs.l_9,self.inputs.w30:self.inputs.l_10,self.inputs.w31:self.inputs.l_11,self.inputs.w32:self.inputs.l_12,self.inputs.w33:self.inputs.l_13,self.inputs.w34:self.inputs.l_14,self.inputs.w35:self.inputs.l_15,self.inputs.w36:self.inputs.l_16,self.inputs.w37:self.inputs.l_17,self.inputs.w38:self.inputs.l_18,self.inputs.w39:self.inputs.l_19,self.inputs.w40:self.inputs.l_20,self.inputs.w41:self.inputs.l_21,self.inputs.w42:self.inputs.l_22}
        dic_general = {self.inputs.g24:self.inputs.l_24,self.inputs.g25:self.inputs.l_25,self.inputs.g26:self.inputs.l_26,self.inputs.g27:self.inputs.l_27,self.inputs.g28:self.inputs.l_28,self.inputs.g29:self.inputs.l_29,self.inputs.g30:self.inputs.l_30,self.inputs.g31:self.inputs.l_31,self.inputs.g32:self.inputs.l_32,self.inputs.g33:self.inputs.l_33,self.inputs.g34:self.inputs.l_34,self.inputs.g35:self.inputs.l_35,self.inputs.g36:self.inputs.l_36,self.inputs.g37:self.inputs.l_37,self.inputs.g38:self.inputs.l_38,self.inputs.g39:self.inputs.l_39,self.inputs.g40:self.inputs.l_40,self.inputs.g41:self.inputs.l_41,self.inputs.g42:self.inputs.l_42,self.inputs.g43:self.inputs.l_43,self.inputs.g44:self.inputs.l_44,self.inputs.g45:self.inputs.l_45,self.inputs.g46:self.inputs.l_46}
        dic_climate = {self.inputs.c6:self.inputs.l_48,self.inputs.c7:self.inputs.l_49,self.inputs.c8:self.inputs.l_50,self.inputs.c9:self.inputs.l_51,self.inputs.c10:self.inputs.l_52}
        dic_buttons_simulation = {self.inputs.s19:self.inputs.l_54,self.inputs.s20:self.inputs.l_55,self.inputs.s21:self.inputs.l_56,self.inputs.s22:self.inputs.l_57,self.inputs.s23:self.inputs.l_58,self.inputs.s24:self.inputs.l_59,self.inputs.s25:self.inputs.l_60,self.inputs.s26:self.inputs.l_61,self.inputs.s27:self.inputs.l_62,self.inputs.s28:self.inputs.l_63,self.inputs.s29:self.inputs.l_64,self.inputs.s30:self.inputs.l_65,self.inputs.s31:self.inputs.l_66,self.inputs.s32:self.inputs.l_67,self.inputs.s33:self.inputs.l_68,self.inputs.s34:self.inputs.l_69,self.inputs.s35:self.inputs.l_70,self.inputs.s36:self.inputs.l_71}
        self.dic_botones = {**dic_buttons_watershed,**dic_general,**dic_climate,**dic_buttons_simulation}
        self.inverted_dict = {value: key for key, value in self.dic_botones.items()} #es el diccionario a la inversa, para que sea más facil luego cambiar los iconos
        #Ahora se crea un diccionario con el nombre de los archivos por cada sección. En el caso de que no haya texto escrito se crearán archivos csv con estos nombres para cada sección. 
        nombres_archivos = ["aqua_pond.csv", "AnnAGNPS_Cell_Data_Section.csv", "classic_gully.csv","AnnAGNPS_Ephemeral_Gully_Data_Section.csv","feedlot.csv","field_pond.csv","impoundment.csv","point_source.csv","AnnAGNPS_Reach_Data_Section.csv","rice.csv","watershed_data.csv","wetland.csv","out_cells.csv","out_feedlots.csv","out_field_ponds.csv","out_classic_gullies.csv","out_eg.csv","out_impoundments.csv","out_point_sources.csv","out_reaches.csv","out_wetlands.csv","aq_pond_schedule.csv","contour.csv","crop.csv","crop_growth.csv","feedlot_man.csv","fert_app.csv","fert_ref.csv","geology.csv","hyd_geom.csv","irr_app.csv","manfield.csv","manoper.csv","mansched.csv","non_crop.csv","pest_app.csv","pest_ref.csv","reach_nutr.csv","rip_buff.csv","run_curve.csv","soil.csv","soil_layer.csv","strip_crop.csv","tile_drain.csv","climate_station.csv","climate_daily.csv","ei_percentage.csv","storm_type_rfd.csv","storm_type_updrc.csv","annaid.csv","glob_error.csv","glob_id.csv","pest_init.csv","pl_cal.csv","rcn_cal.csv","sim_period.csv","soil_init.csv","rusle2.csv","out_glob.csv","out_csv.csv","out_dp.csv","out_input.csv","out_sim.csv","out_aa.csv","out_ev.csv","out_tbl.csv","out_minmax.csv"]
        self.dic_boton_archivo = {}
        for i, clave in enumerate(self.dic_botones.keys()):
            if i < len(nombres_archivos):
                self.dic_boton_archivo[clave] = nombres_archivos[i]     
        #Ahora se cambian los colores de las líneas y el icono de los botones
        self.lines_dialog = [self.inputs.l_2, self.inputs.l_3, self.inputs.l_4, self.inputs.l_5, self.inputs.l_6, self.inputs.l_7, self.inputs.l_8, self.inputs.l_9, self.inputs.l_10, self.inputs.l_11, self.inputs.l_12, self.inputs.l_13, self.inputs.l_14, self.inputs.l_15, self.inputs.l_16, self.inputs.l_17, self.inputs.l_18, self.inputs.l_19, self.inputs.l_20, self.inputs.l_21, self.inputs.l_22,self.inputs.l_24, self.inputs.l_25, self.inputs.l_26, self.inputs.l_27, self.inputs.l_28, self.inputs.l_29, self.inputs.l_30, self.inputs.l_31, self.inputs.l_32, self.inputs.l_33, self.inputs.l_34, self.inputs.l_35, self.inputs.l_36, self.inputs.l_37, self.inputs.l_38, self.inputs.l_39, self.inputs.l_40, self.inputs.l_41, self.inputs.l_42, self.inputs.l_43, self.inputs.l_44, self.inputs.l_45, self.inputs.l_46, self.inputs.l_48, self.inputs.l_49, self.inputs.l_50, self.inputs.l_51, self.inputs.l_52, self.inputs.l_54, self.inputs.l_55, self.inputs.l_56, self.inputs.l_57, self.inputs.l_58, self.inputs.l_59, self.inputs.l_60, self.inputs.l_61, self.inputs.l_62, self.inputs.l_63, self.inputs.l_64, self.inputs.l_65, self.inputs.l_66, self.inputs.l_67, self.inputs.l_68, self.inputs.l_69, self.inputs.l_70, self.inputs.l_71]
        self.dic_lines_search = {self.inputs.l_2:self.inputs.w1,self.inputs.l_3:self.inputs.w2,self.inputs.l_4:self.inputs.w3,self.inputs.l_5:self.inputs.w4,self.inputs.l_6:self.inputs.w5,self.inputs.l_7:self.inputs.w6,self.inputs.l_8:self.inputs.w7,self.inputs.l_9:self.inputs.w8,self.inputs.l_10:self.inputs.w9,self.inputs.l_11:self.inputs.w10,self.inputs.l_12:self.inputs.w11,self.inputs.l_13:self.inputs.w12,self.inputs.l_14:self.inputs.w13,self.inputs.l_15:self.inputs.w14,self.inputs.l_16:self.inputs.w15,self.inputs.l_17:self.inputs.w16,self.inputs.l_18:self.inputs.w17,self.inputs.l_19:self.inputs.w18,self.inputs.l_20:self.inputs.w19,self.inputs.l_21:self.inputs.w20,self.inputs.l_22:self.inputs.w21,self.inputs.l_24:self.inputs.g1,self.inputs.l_25:self.inputs.g2,self.inputs.l_26:self.inputs.g3,self.inputs.l_27:self.inputs.g4,self.inputs.l_28:self.inputs.g5,self.inputs.l_29:self.inputs.g6,self.inputs.l_30:self.inputs.g7,self.inputs.l_31:self.inputs.g8,self.inputs.l_32:self.inputs.g9,self.inputs.l_33:self.inputs.g10,self.inputs.l_34:self.inputs.g11,self.inputs.l_35:self.inputs.g12,self.inputs.l_36:self.inputs.g13,self.inputs.l_37:self.inputs.g14,self.inputs.l_38:self.inputs.g15,self.inputs.l_39:self.inputs.g16,self.inputs.l_40:self.inputs.g17,self.inputs.l_41:self.inputs.g18,self.inputs.l_42:self.inputs.g19,self.inputs.l_43:self.inputs.g20,self.inputs.l_44:self.inputs.g21,self.inputs.l_45:self.inputs.g22,self.inputs.l_46:self.inputs.g23,self.inputs.l_48:self.inputs.c1,self.inputs.l_49:self.inputs.c2,self.inputs.l_50:self.inputs.c3,self.inputs.l_51:self.inputs.c4,self.inputs.l_52:self.inputs.c5,self.inputs.l_54:self.inputs.s1,self.inputs.l_55:self.inputs.s2,self.inputs.l_56:self.inputs.s3,self.inputs.l_57:self.inputs.s4,self.inputs.l_58:self.inputs.s5,self.inputs.l_59:self.inputs.s6,self.inputs.l_60:self.inputs.s7,self.inputs.l_61:self.inputs.s8,self.inputs.l_62:self.inputs.s9,self.inputs.l_63:self.inputs.s10,self.inputs.l_64:self.inputs.s11,self.inputs.l_65:self.inputs.s12,self.inputs.l_66:self.inputs.s13,self.inputs.l_67:self.inputs.s14,self.inputs.l_68:self.inputs.s15,self.inputs.l_69:self.inputs.s16,self.inputs.l_70:self.inputs.s17,self.inputs.l_71:self.inputs.s18}
        #Se pone la dirección relativa de los iconos
        icon_relative_path_document = "images/document.svg"
        icon_relative_path_createdocument = "images/create_document.svg"
        icon_relative_path_search = "images/search.svg"
        plugin_directory = os.path.dirname(os.path.realpath(__file__))
        self.plugin_directory=plugin_directory
        self.icon_path_document = os.path.join(plugin_directory, icon_relative_path_document)
        self.icon_path_createdocument = os.path.join(plugin_directory, icon_relative_path_createdocument)
        self.icon_path_search = os.path.join(plugin_directory, icon_relative_path_search)
        #Bucle para añadir los iconos y estilos en los inputs de AnnANGPS
        for i in self.lines_dialog:
            if i.text()!="":
                i.setStyleSheet("QLineEdit { background-color: rgb(196, 240, 119) ; }")
                self.inverted_dict[i].setIcon(QIcon(self.icon_path_document))
            else:
                i.setStyleSheet("QLineEdit { background-color: rgb(250, 159, 160) ; }")
                self.inverted_dict[i].setIcon(QIcon(self.icon_path_createdocument))
            self.dic_lines_search[i].setIcon(QIcon(self.icon_path_search))
            self.dic_lines_search[i].clicked.connect(lambda _, b=i: self.search_document(b))
            i.textChanged.connect(lambda _, b=i: self.change_colors(b))
            i.textChanged.connect(lambda _, b=i: self.change_icons(b))
        
        #Cambiar el borde de la línea de texto si no existe la ruta
        self.border = False #no están puestos los bordes
        self.inputs.path.clicked.connect(self.path_exist)
        
        #Poner el icono de descargar desde master file
        master_icon = os.path.join(plugin_directory, "images/import_master.svg")
        self.inputs.pb_master.setIcon(QIcon(master_icon))
        
        #Poner el icono de descargar desde path exists
        path_icon = os.path.join(plugin_directory, "images/path_exist.svg")
        self.inputs.path.setIcon(QIcon(path_icon))
        
        #Icono de que no existe output
        path_icon = os.path.join(plugin_directory, "images/no_file.svg")
        self.output.file_ex.setIcon(QIcon(path_icon))
        
        #Icono de filtro en los outputs
        path_icon = os.path.join(plugin_directory, "images/filter.svg")
        self.output.filter_run.setIcon(QIcon(path_icon))
        
        #Abrir los archivos de los inputs de AnnAGNPS cuando se le dé al botón correspondiente. 
        for i in self.dic_botones.keys():
            i.clicked.connect(lambda _, b=i: self.open_file(b))
        
        #Hacer que cuando se pregunte si quieres que se sobreescriba si le das a Yes que se sobreescriba y se le das a No entonces que no
        self.overwrite.pushButton.clicked.connect(self.overwrite_file)
        self.overwrite.pushButton_2.clicked.connect(self.not_overwrite_file)
        
        #Hacer que cuando se cree un archivo nuevo aparezca con las columnas ya puestas
        #Para ello primero en cada sección se ponen las columnas necesarias
        #WATERSHED
        apond_col = ["Pond_ID","Cell_ID", "Pond_Area", "Pond_Depth", "Seepage_Rate", "Sediment_Delivery_Ratio", "Relative_Rotation_Year", "Mgmt_Schd_ID", "OC_Calib_Fctr", "N_Calib_Fctr", "P_Calib_Fctr", "Erosion_Calib_Fctr", "Input_Units_Code"]
        cell_col = ["Cell_ID", "Soil_ID", "Mgmt_Field_ID", "Reach_ID", "Reach_Location_Code", "Cell_Area", "Time_of_Conc", "Avg_Elevation", "RCN_Calib_ID", "Avg_Land_Slope", "Aspect", "RUSLE_ls_Fctr", "RCN_Rtn_Calib_Fctr", "Secondary_Climate_File_ID", "Sheet_Flow_Mannings_n", "Geology_ID", "Conc_Flow_Slope", "Conc_Flow_Length", "Hydraulic_Geom_ID", "Conc_Flow_Hydraulic_Depth", "Conc_Flow_Mannings_n", "Sheet_Flow_Slope", "Sheet_Flow_Length", "Shallow_Conc_Flow_Slope", "Shallow_Conc_Flow_Length", "Delivery_Ratio", "Constant_USLE_C_Fctr", "Constant_USLE_P_Fctr", "All_OC_Calib_Fctr", "All_N_Calib_Fctr", "All_P_Calib_Fctr", "Sheet_and_Rill_Erosion_Calib_Fctr", "Gullies_Erosion_Calib_Fctr", "Input_Units_Code"]
        classic_gully_col = ["Gully_ID", "Cell_ID", "Reach_ID", "Soil_ID", "Cell_Drainage_Area", "Reach_Drainage_Area", "Headcut_Depth", "Erosion_Coef", "Erosion_exp", "Delivery_Ratio", "Mgmt_Field_ID", "Cell_Drainage_Subarea", "Load_Calib_Fctr", "Rainfall/Runoff_Indicator", "Units_Indicator", "Gully_Location_Code", "OC_Calib_Fctr", "N_Calib_Fctr", "P_Calib_Fctr", "Erosion_Calib_Fctr", "Input_Units_Code"]
        eg_col = ["Gully_ID", "Cell_ID", "Reach_ID", "Soil_ID", "Drainage_Area_to_Mouth", "Local_Drainage_Area", "Gully_Slope", "Critical_Shear_Stress", "Gully_Location_Code", "Mgmt_Field_ID", "Erosion_Depth", "Cells_Drainage_Subcell", "Hydraulic_Geometry_ID", "Width_Nachtergaele", "Width_Hydraulic_Geometry", "Width_Non-submerging_Tailwater", "Width_Woodwards_Equilibrium", "Width_Woodwards_Ultimate", "Width_Wells_Eq.9", "Delivery_Ratio", "Mannings_n", "Replant_Period", "OC_Calib_Fctr", "N_Calib_Fctr", "P_Calib_Fctr", "Erosion_Calib_Fctr", "Headcut_Migration_Barrier", "Headcut_Dtach/Erod_Coef_a", "Headcut_Dtach/Erod_Exp_Coef_b", "Max_Trapping_Efficiency", "Width_Wells_Eq.8", "Width_reserved_i", "Width_reserved_j", "Width_reserved_k", "Input_Units_Code"]
        feedlot_col = ["Feedlot_ID", "Feedlot_Mgmt_ID", "Open_Area", "Paved_Ratio", "Roof_Area", "Upslope_Area", "Initial_N", "Initial_P", "Initial_OC", "Delta_N", "Delta_P", "Delta_OC", "Max_N", "Max_P", "Max_OC", "Pack_N", "Pack_P", "Pack_OC", "OC_Calib_Fctr", "N_Calib_Fctr", "P_Calib_Fctr", "Erosion_Calib_Fctr", "Cell_ID", "Cell_Buffer_Length", "Input_Units_Code"]
        field_pond_col = ["Pond_ID", "Cell_ID", "Pond_Area", "Number_of_Rotation_Years", "Number_of_Gate_Operations", "Delivery_Ratio", "Volume_of_Release_Water", "Drain_Time", "Release_Rate", "Sediment_Conc", "Clay_Content", "Silt_Content", "N_Conc", "P_Conc", "OC_Conc", "Pesticide_Reference_ID", "Pesticide_Conc", "OC_Calib_Fctr", "N_Calib_Fctr", "P_Calib_Fctr", "Erosion_Calib_Fctr", "Input_Units_Code"]
        impoundment_col = ["Impoundment_ID", "Infiltration", "Seepage", "Permanent_Pool_Depth", "Volume_Coef", "Volume_Exp", "Discharge_Coef", "Discharge_Exp", "Sed_Clean_Out_Depth", "Sed_Clean_Out_Year", "Reach_ID", "Input_Units_Code"]
        point_source_col =  ["Point_Source_ID", "Cell_ID", "Point_Flow", "Point_N", "Point_P", "Point_OC", "OC_Calib_Fctr", "N_Calib_Fctr", "P_Calib_Fctr", "Erosion_Calib_Fctr", "Input_Units_Code"]
        reach_col = ["Reach_ID", "Receiving_Reach", "Vegetation_Code", "Elevation", "Slope", "Mannings_n", "Infiltration_Rate", "Hydraulic_Geom_ID", "Length", "Top_Width", "Flow_Depth", "Valley_Width", "Valley_Mannings_n", "Start_Diversion", "Stop_Diversion", "Travel_Time", "Clay_Scour_Code", "Silt_Scour_Code", "Sand_Scour_Code", "Small_Agg_Scour_Code", "Large_Agg_Scour_Code", "Valley_Clay_Scour_Code", "Valley_Silt_Scour_Code", "Valley_Sand_Scour_Code", "Valley_Small_Agg_Scour_Code", "Valley_Large_Agg_Scour_Code", "Delivery_Ratio", "Input_Units_Code"]
        rice_col = ["RiceWQ_ID", "Cell_ID", "Pesticide_Reference_ID", "Intersected_Area", "Suspended_Sediment_Concentration", "Organic_Carbon_Partition_Coef", "Treated_Area_Filename", "RiceWQ_Loadings_Filename", "Carbon_to_Clay_Ratio"]
        watershed_col = ["Wshd_Name", "Wshd_Description", "Wshd_Location", "Latitude", "Longitude"]
        wetland_col =["Wetland_ID", "Reach_ID", "Wetland_Area", "Initial_Water_Depth", "Min_Water_Depth", "Max_Water_Depth", "Water_Temperature", "Potential_Daily_Infiltration", "Weir_Coef", "Weir_Width", "Weir_Height", "Soluble_N_Conc", "Nitrate-N_Loss_Rate", "Nitrate-N_Loss_Rate_Coef", "Temperature_Coef", "Weir_Exp", "Input_Units_Code"]
        out_cell_col = ["Cell_ID"]
        out_feedlot_col = ["Feedlot_ID"]
        out_field_pond_col = ["Field_Pond_ID"]
        out_classic_gullies_col = ["Classic_Gully_ID"]
        out_eg_col = ["Ephemeral_Gully_ID"]
        out_impoundment_col = ["Impoundment_ID"]
        out_point_source_col = ["Point_Source_ID"]
        out_reach_col = ["Reach_ID"]
        out_wet_col = ["Wetland_ID"]
        dic_bc_watershed = {self.inputs.w22: apond_col, self.inputs.w23: cell_col, self.inputs.w24: classic_gully_col, self.inputs.w25: eg_col, self.inputs.w26: feedlot_col, self.inputs.w27: field_pond_col, self.inputs.w28: impoundment_col, self.inputs.w29: point_source_col, self.inputs.w30: reach_col, self.inputs.w31: rice_col, self.inputs.w32: watershed_col, self.inputs.w33: wetland_col, self.inputs.w34: out_cell_col, self.inputs.w35: out_feedlot_col, self.inputs.w36: out_field_pond_col, self.inputs.w37: out_classic_gullies_col, self.inputs.w38: out_eg_col, self.inputs.w39: out_impoundment_col, self.inputs.w40: out_point_source_col, self.inputs.w41: out_reach_col, self.inputs.w42: out_wet_col}
        #GENERAL
        apond_schedule_col = ["Pond_Mgmt_Schd_ID", "Month", "Day", "Year", "Water_Operation_Code", "Aquaculture_ID", "Crop_ID", "Planting_Type_Code", "Gate_Status", "Max_Pool_Depth", "Min_Pool_Depth", "Fill/Release_Vol", "Fill/Drain_Time", "Fill/Release_Rate", "Fill/Drain_All_Code", "Total_Sed_Conc", "Clay_Content", "Silt_Content", "Total_N", "Dissolved_N", "Total_P", "Dissolved_P", "Num_Pest_Apps", "Season_Adjust_Conc", "Sed_Conc_Winter", "Total_N_Winter", "Dissolved_N_Winter", "Total_P_Winter", "Dissolved_P_Winter", "Sed_Conc_Spring", "Total_N_Spring", "Dissolved_N_Spring", "Total_P_Spring", "Dissolved_P_Spring", "Sed_Conc_Summer", "Total_N_Summer", "Dissolved_N_Summer", "Total_P_Summer", "Dissolved_P_Summer", "Sed_Conc_Autumn", "Total_N_Autumn", "Dissolved_N_Autumn", "Total_P_Autumn", "Dissolved_P_Autumn", "Input_Units_Code"]
        contour_col = ["Contour_ID", "Ridge_Height_Code", "Furrow_Slope", "Disturbed_Cover", "Consolidated_Cover", "Input_Units_Code"]
        crop_col = ["Crop_ID", "Yield_Units_Harvested", "Residue_Mass_Ratio", "Surface_Decomp", "Sub-surface_Decomp", "USLE_C_Fctr", "Moisture_Depletion", "Residue_Adjust_Amt", "Crop_Residue_30%", "Crop_Residue_60%", "Crop_Residue_90%", "Annual_Crop_Code", "Legume_Code", "Senescence_Code", "Yield_Unit_Name", "Yield_Unit_Mass", "Harvest_C-N_Ratio", "Pre-Harvest_C-N_Ratio", "Harvest_Water", "N_Uptake", "P_Uptake", "Harvest_C-P_Ratio", "Pre-Harvest_C-P_Ratio", "Growth_Time_Ini", "Growth_Time_Dev", "Growth_Time_Mat", "Growth_Time_Sen", "Growth_N_Uptake_Ini", "Growth_N_Uptake_Dev", "Growth_N_Uptake_Mat", "Growth_N_Uptake_Sen", "Growth_P_Uptake_Ini", "Growth_P_Uptake_Dev", "Growth_P_Uptake_Mat", "Growth_P_Uptake_Sen", "Basal_Crop_Coef_Ini", "Basal_Crop_Coef_Dev", "Basal_Crop_Coef_Mid", "Basal_Crop_Coef_End", "Basal_Crop_Coef_Climate_Adjust", "Input_Units_Code"]
        crop_growth_col = ["Crop_Growth_ID", "Root_Mass", "Canopy_Cover", "Rain_Fall_Height", "Input_Units_Code"]
        feedlot_man_col =  ["Mgmt_ID", "Month", "Day", "Year", "Pack_Remove_Ratio", "Pack_Start_N", "Pack_Start_P", "Pack_Start_OC", "Pack_Change_N", "Pack_Change_P", "Pack_Change_OC", "Input_Units_Code"]
        fert_app_col =  ["Application_ID", "Name_ID", "Application_Rate", "Depth", "Mixing_Code", "Input_Units_Code"]
        fert_ref_col =  ["Reference_ID", "Nitrite", "Nitrate", "Inorganic_N", "Organic_N", "Ammonia", "Mineral_Ammonia", "Elemental_P", "Soluble_P", "Inorganic_P", "Organic_P", "Organic_Matter", "Consistency_Code"]
        geology_col = ["Geology_ID", "Delay_Time", "Water_Table", "Aquifer_Sat_Hyd_Conduct", "Vadose_Sat_Hyd_Conduct", "Porosity", "Field_Capacity", "Specific_Yield", "Thickness", "Soluble_N", "Soluble_P", "Input_Units_Code"]
        hydgeom_col = ["Hydraulic_Geom_ID", "Channel_Length_Coef", "Channel_Length_Exp", "Channel_Width_Coef", "Channel_Width_Exp", "Channel_Depth_Coef", "Channel_Depth_Exp", "Valley_Width_Coef", "Valley_Width_Exp"]
        irr_app_col = ["Season_End_Month", "Season_End_Day", "Season_End_Year", "Method_Code", "Water_Source", "Cycle_Duration", "Amount_Lost", "Application_Rate", "Tailwater_Recovery", "Depletion_Lower_Limit", "Application_Amount", "Area_Fraction", "Interval_Number", "Interval_Days", "Chemical_Multiple", "Sediment_Rate", "Depletion_Upper_Limit", "Input_Units_Code"]
        manfield_col =["Field_ID", "Landuse_Type_ID", "Mgmt_Schd_ID", "Greg_Yr_for_1st_Yr_of_Rotation", "Percent_Rock_Cover", "Interrill_Erosion_Code", "Random_Roughness", "Terrace_Horizontal_Distance", "Terrace_Grade", "Tile_Drain_ID", "Input_Units_Code"]
        manoper_col = ["Mgmt_Operation_ID", "Effect_Code_01", "Effect_Code_02", "Effect_Code_03", "Effect_Code_04", "Effect_Code_05", "Residue_Cover_Remaining", "Residue_Weight_Remaining", "Area_Disturbed", "Initial_Random_Roughness", "Final_Random_Roughness", "Operation_Tillage_Depth", "Added_Surface_Residue", "Surface_Decomp", "Subsurface_Decomp", "Surface_Residue_30%", "Surface_Residue_60%", "Surface_Residue_90%", "Input_Units_Code"]
        mansched_col =["Mgmt_Schd_ID", "Event_Month", "Event_Day", "Event_Year", "Contour_ID", "New_Crop_ID", "Strip_Crop_ID", "New_Non-Crop_ID", "Curve_Number_ID", "Post_Event_Mannings_n", "Post_Event_Surface_Constant", "Operation_Residue_Change", "Fertilizer_Application_ID", "Irrigation_Application_ID", "Mgmt_Operation_ID", "Tile_Drain_Controlled_Status", "Tile_Drain_Controlled_Depth", "Input_Units_Code", "Pest_App_ID_1", "Pest_App_ID_2", "Pest_App_ID_3", "Pest_App_ID_4", "Pest_App_ID_5"]
        non_crop_col = ["Non-Crop_ID", "Non-Crop_Description", "Annual_Root_Mass", "Annual_Cover_Ratio", "Annual_Rain_Fall_Height", "Surface_Cover_Residue", "USLE_C-Fctr", "Basal_Crop_Coef_Mid", "Growing_Season_Start_Month", "Growing_Season_Start_Day", "Growing_Season_End_Month", "Growing_Season_End_Day", "Basal_Crop_Coef_Climate_Adjust", "Input_Units_Code"]
        pestapp_col = ["Application_ID", "Reference_ID", "Application_Rate", "Depth", "Mixing_Code", "Foliage_Fraction", "Soil_Fraction", "Input_Units_Code"]
        pest_ref_col =  ["Pesticide_Reference_ID", "Solubility", "Partition", "Soil_Half-life", "Foliage_Half-life", "Washoff", "Metabolite_ID", "Metabolite_Transformation", "Reach_Half-life"]
        reach_nutrient_col =  ["N_Half-life", "P_Half-life", "OC_Half-life"]
        rip_buff_col =  ["Buffer_ID", "Location_ID", "Vegetative_Type", "Buffer_Slope", "Max_Trap_Efficiency", "Eff_Wdth_Thru_Buffer", "Eff_Wdth_Along_Buffer", "Buffer_Location_Code", "Drainage_Area_to_Buffer", "Actual_Trap_Efficiency_Clay", "Actual_Trap_Efficiency_Silt", "Actual_Trap_Efficiency_Sand", "Actual_Trap_Efficiency_Sm_Agg", "Actual_Trap_Efficiency_Lg_Agg", "Fraction_Trapped_Clay", "Fraction_Trapped_Silt", "Fraction_Trapped_Sand", "Fraction_Trapped_Sm_Agg", "Fraction_Trapped_Lg_Agg", "Input_Units_Code"]
        run_curve_col = ["Curve_Number_ID", "CN_A", "CN_B", "CN_C", "CN_D"]
        soil_col = ["Soil_ID", "Hydrologic_Soil_Group", "K_Factor", "Albedo", "Time_to_Consolidation", "Impervious_Depth", "Specific_Gravity", "Initial_Soil_Conditions_ID", "Soil_Name", "Soil_Texture", "Number_of_Soil_Layers", "Input_Units_Code"]
        soil_layer_col = ["Soil_ID", "Layer_Number", "Layer_Depth", "Bulk_Density", "Clay_Ratio", "Silt_Ratio", "Sand_Ratio", "Rock_Ratio", "Very_Fine_Sand_Ratio", "CaCO3_Content", "Saturated_Conductivity", "Field_Capacity", "Wilting_Point", "Volcanic_Code", "Base_Saturation", "Unstable_Aggregate_Ratio", "pH", "Organic_Matter_Ratio", "Organic_N_Ratio", "Inorganic_N_Ratio", "Organic_P_Ratio", "Inorganic_P_Ratio", "Soil_Structure_Code", "Input_Units_Code"]
        strip_crop_col =  ["Strip_Crop_ID", "P_Factor", "Delivery_Ratio"]
        tile_drain_col = ["Tile_Drain_ID", "Drain_Rate", "Invert_Depth", "Input_Units_Code"]
        dic_bc_general =  {self.inputs.g24: apond_schedule_col, self.inputs.g25: contour_col, self.inputs.g26: crop_col, self.inputs.g27: crop_growth_col, self.inputs.g28: feedlot_man_col, self.inputs.g29: fert_app_col, self.inputs.g30: fert_ref_col, self.inputs.g31: geology_col, self.inputs.g32: hydgeom_col, self.inputs.g33: irr_app_col, self.inputs.g34: manfield_col, self.inputs.g35: manoper_col, self.inputs.g36: mansched_col, self.inputs.g37:non_crop_col , self.inputs.g38: pestapp_col , self.inputs.g39: pest_ref_col , self.inputs.g40:reach_nutrient_col , self.inputs.g41: rip_buff_col , self.inputs.g42:run_curve_col , self.inputs.g43:soil_col , self.inputs.g44:soil_layer_col , self.inputs.g45:strip_crop_col ,self.inputs.g46:tile_drain_col}
        #CLIMATE
        climate_station_col =  ["Version", "Input_Units_Code", "Climate_Station_Name", "Beginning_Climate_Date", "Ending_Climate_Date", "Latitude", "Longitude", "Elevation", "Temperature_Lapse_Rate", "Precipitation_N", "Global_Storm_Type_ID", "1st_Elevation_Difference", "1st_Elevation_Rain_Factor", "2nd_Elevation_Difference", "2nd_Elevation_Rain_Factor", "2_Yr_24_hr_Precipitation", "Calibration_or_Areal_Correction_Coefficient", "Calibration_or_Areal_Correction_Exponent", "Minimum_Interception_Evaporation", "Maximum_Interception_Evaporation", "Winter_Storm_Type_ID", "Spring_Storm_Type_ID", "Summer_Storm_Type_ID", "Autumn_Storm_Type_ID"]
        climate_daily_col =["Month", "Day", "Year", "Max_Air_Temperature", "Min_Air_Temperature", "Precip", "Dew_Point", "Sky_Cover", "Wind_Speed", "Wind_Direction", "Solar_Radiation", "Storm_Type_ID", "Potential_ET", "Actual_ET", "Actual_EI", "Input_Units_Code"]
        ei_per_col = ["EI_Pct_01", "EI_Pct_02", "EI_Pct_03", "EI_Pct_04", "EI_Pct_05", "EI_Pct_06", "EI_Pct_07", "EI_Pct_08", "EI_Pct_09", "EI_Pct_10", "EI_Pct_11", "EI_Pct_12", "EI_Pct_13", "EI_Pct_14", "EI_Pct_15", "EI_Pct_16", "EI_Pct_17", "EI_Pct_18", "EI_Pct_19", "EI_Pct_20", "EI_Pct_21", "EI_Pct_22", "EI_Pct_23", "EI_Pct_24"]
        storm_type_rfd_col = [""]
        storm_type_updrc_col = [""]
        dic_bc_climate = {self.inputs.c6:climate_station_col,self.inputs.c7:climate_daily_col,self.inputs.c8:ei_per_col,self.inputs.c9:storm_type_rfd_col,self.inputs.c10:storm_type_updrc_col}
        #SIMULATION
        annaid_col = ["Version","Input_Units","Output_Units","CCHE1D_Output_Units","Screen_Output_Units"]
        global_error_col = ["Keyword_ID", "Warning_Min", "Warning_Max"]
        global_ids_col = ["Hdct_Detachment_Coef_a", "Hdct_Detachment_Exp_Coef_b", "Urban_Repair_Month", "Urban_Repair_Day", "Urban_Repair_Year", "Cropland_Repair_Month", "Cropland_Repair_Day", "Cropland_Repair_Year", "Forest_Repair_Month", "Forest_Repair_Day", "Forest_Repair_Year", "Pasture_Repair_Month", "Pasture_Repair_Day", "Pasture_Repair_Year", "Rangeland_Repair_Month", "Rangeland_Repair_Day", "Rangeland_Repair_Year", "Hdct_Erodibility_Coef_a", "Hdct_Erodibility_Exp_Coef_b", "Width_Nachtergaele", "Width_Hydraulic_Geometry", "Width_Non-submerging_Tailwater", "Width_Woodwards_Equilibrium", "Width_Woodwards_Ultimate", "Width_Wells_Eq.9", "Erosion_Vrfy", "Hydrograph_Vrfy", "Nickpoint_Vrfy", "Repair_Dates_Vrfy", "Sed_Yield_to_Gully_Mouth_Vrfy", "Sed_Yield_to_Rcvg_Reach_Vrfy", "Min_Interception_Evaporation", "Max_Interception_Evaporation", "Detention_Coef_a", "Detention_Coef_b", "RCN_Convergence_Tolerance", "RCN_Max_Iterations", "Avbl_Soil_Moist_Ratio_AMC_II", "Max_Avbl_Sed_Conc_for_Sht_Flw", "Max_Avbl_Sed_Conc_for_Conc_Flw", "AA_Unit_Area_Baseflow", "RCN_Calib_Only", "Calculate_Baseflow", "FAO_ET_Enhancement", "Basal_Crop_Coef_Climate_Adjust", "Wshd_Storm_Type_ID", "Dflt_Geology_ID", "Dflt_Hydraulic_Geom_ID", "Dflt_Init_Soil_Conditions_ID", "Dflt_Crop_RCN_ID", "Dflt_Non-Crop_RCN_ID", "Width_Wells_Eq.8", "Width_Reserved_i", "Width_Reserved_j", "Width_Reserved_k", "Critical_Shear_Stress", "RUSLE2_Flag", "Dflt_RUSLE2_ID", "Input_Units_Code"]
        pesticide_initial_col = ["Initial_Pesticide_ID","Crop_Initial_Amount_1","Crop_Initial_Amount_2","Non-Crop_Initial_Amount_1", "Non-Crop_Initial_Amount_2"]
        pl_calibration_col = ["OC_All_Sources", "OC_Sheet_and_Rill", "OC_Feedlot", "OC_Point_Source", "OC_Gully", "OC_Pond", "OC_Irrigation", "N_All_Sources", "N_Sheet_and_Rill", "N_Feedlot", "N_Point_Source", "N_Gully", "N_Pond", "N_Irrigation", "P_All_Sources", "P_Sheet_and_Rill", "P_Feedlot", "P_Point_Source", "P_Gully", "P_Pond", "P_Irrigation", "Sediment_All_Sources", "Sediment_Sheet_and_Rill", "Sediment_Feedlot", "Sediment_Point_Source", "Sediment_Gully", "Sediment_Pond", "Sediment_Irrigation"]
        rcn_col = ["RCN_Calib_ID","Target_AA_Direct_Runoff_Load","RCN_Retention_Fctr","Reach_ID_Site","Reach_Ratio","Avbl_Soil_Moist_AMC_II","Input_Units_Code"]
        sim_col = ["Simulation_Begin_Month", "Simulation_Begin_Day", "Simulation_Begin_Year", "Simulation_End_Month", "Simulation_End_Day", "Simulation_End_Year", "Rainfall_Fctr", "10-Year_EI", "EI_Number", "Irrigation_Climate_Code", "Soil_Moisture_Steps", "Annual_K_Fctr_Code", "Variable_K_Fctr_Code", "Number_Init_Years", "Init_Method_Code", "Winter_Bouts", "Input_Units_Code"]
        soil_initial_col = ["Initial_Soil_Conditions_ID", "Inorganic_N_1 for layer 1 and Inorganic_N_2 for layer 2", "Inorganic_P_1 for layer 1 and Inorganic_P_2 for layer 2", "Soil_Moisture_1 for layer 1 and Soil_Moisture_2 for layer 2", "Organic_Matter_1 for layer 1 and Organic_Matter_2 for layer 2", "Organic_N_1 for layer 1 and Organic_N_2 for layer 2", "Organic_P_1 for layer 1 and Organic_P_2 for layer 2", "Surface_Residue", "Mannings_n", "Snow_Depth", "Snow_Density", "Surface_Constant", "Input_Units_Code"]
        rusle2_col = ["RUSLE2_ID","RUSLE2_Filename","RUSLE2_Erosion_Flag"]
        out_global_col =["Glbl_All_V3_csv", "Glbl_All_V3_dpp", "Glbl_All_V3_npt", "Glbl_All_V3_sim", "Glbl_All_V3_txt", "Log_to_File", "Log_to_Screen", "Warning_File", "V1/2_Output_Files", "Reserved", "Glbl_All_Cells", "Glbl_All_Feedlots", "Glbl_All_Fld_Ponds", "Glbl_All_Gullies", "Glbl_All_Pt_Srcs", "Glbl_All_Reaches", "Glbl_All_Impound", "Glbl_All_Wetlands", "Glbl_All_AA_Nutr", "Glbl_All_AA_Pest", "Reserved", "Reserved", "Glbl_All_AA_Sed", "Glbl_All_AA_Wtr", "Glbl_All_EV_Nutr", "Glbl_All_EV_Pest", "Glbl_All_EV_Sed", "Glbl_All_EV_Wtr", "Reserved", "Reserved", "Glbl_All_V2/3_Mass", "Glbl_All_V2/3_Ratio", "Glbl_All_V2/3_UA", "Reserved", "V2_Concepts", "Reserved", "V2_AA", "V2_EV", "V1_AA", "V1_EV"]
        out_csv_col =  ["All_Evt_Lds_Cell_to_DS_Rchs", "All_AA", "All_Events", "All_N", "All_OC", "All_Pesticides", "All_P", "All_Sediment", "All_Water", "AA_N_Ld_Cel_to_DS_Rchs", "AA_N_Ld_in_Rchs", "AA_N_Yld_Cel_to_Rcv_Rch", "AA_OC_Ld_Cel_to_DS_Rchs", "AA_OC_Ld_in_Rchs", "AA_OC_Yld_Cel_to_Rc_v_Rch", "AA_Pest_Ld_Cel_to_DS_Rchs", "AA_Pest_Ld_in_Rchs", "AA_Pest_Yld_Cel_to_Rcv_Rch", "AA_P_Ld_Cel_to_DS_Rchs", "AA_P_Ld_in_Rchs", "AA_P_Yld_Cel_to_Rcv_Rch", "AA_BB_Eros_in_Rch", "AA_BB_Ld_in_DS_Rchs", "AA_Eros_in_Cels", "AA_Gly_Yld_Cel_to_Rcv_Rch", "AA_LS_Eros_in_Cels", "AA_LS_Ld_Cels_to_DS_Rchs", "AA_LS_Ld_in_DS_Rchs", "AA_LS_Yld_Cel_to_Rc_v_Rch", "AA_Rill_Eros_in_Cels", "AA_SR_Yld_Cel_to_Rc_v_Rch", "AA_Wtr_Ld_Cel_to_DS_Rchs", "AA_Wtr_Ld_in_DS_Rc_hs", "AA_Wtr_Yld_Cel_to_Rcv_Rch", "N_Evt_Ld_Cel_to_DS_Rchs", "N_Evt_Ld_in_Rchs", "N_Evt_Yld_Cel_to_Rcv_Rch", "OC_Evt_Ld_Cel_to_DS_Rchs", "OC_Evt_Ld_in_Rchs", "OC_Evt_Yld_Cel_to_Rc_v_Rch", "Pest_Evt_Ld_Cel_to_DS_Rchs", "Pest_Evt_Ld_in_Rchs", "Pest_Evt_Yld_Cel_to_Rcv_Rch", "P_Evt_Ld_Cel_to_DS_Rchs", "P_Evt_Ld_in_Rchs", "P_Evt_Yld_Cel_to_Rcv_Rch", "Sed_Evt_BB_Eros_in_Rch", "Sed_Evt_BB_Ld_in_DS_Rchs", "Sed_Evt_Gly_Eros_in_Cels", "Sed_Evt_Gly_Yld_Cel_to_Rcv_Rch", "Sed_Evt_LS_Eros_in_Cels", "Sed_Evt_LS_Ld_Cel_to_DS_Rchs", "Sed_Evt_LS_Ld_in_Rc_hs", "Sed_Evt_LS_Yld_Cel_to_Rcv_Rch", "Sed_Evt_SR_Eros_in_C_els", "Sed_Evt_SR_Yld_Cel_to_Rcv_Rch", "Wtr_Evt_Ld_Cel_to_DS_Rchs", "Wtr_Evt_Ld_in_DS_Rc_hs", "Wtr_Evt_Pk_Disch_in_DS_Rch", "Wtr_Evt_Yld_Cel_to_Rcv_Rch","Wtr_Evt_Baseflow"]
        out_dpp_col =["Acc_Setup", "Cell_Initial", "Cell_TOC", "Crp_Grwth", "Data_Prep_Pointers", "Weather", "Opr_Rotation", "Pest_Metabolite", "Process_Flag", "Quadrature", "Hydraulic_Geom", "Rch_Routing", "Rch_TOC", "RUSLE_C_Fctr", "RUSLE_C_Fctr_SC", "Canopy_Cover", "Crp_Residue", "Dead_Roots", "PreProc_C_Fctr", "Dom_Contour", "EI_Pcts", "RUSLE_Grwth_Days", "RUSLE_Init_Loc_Oprs", "RUSLE_K_Fctr", "Reserved", "RUSLE_Non-,crp_C_Fctr", "RUSLE_Num_SLyr_SR es", "RUSLE_P_Fctr", "RUSLE_P_Fctr_Cntrs", "RUSLE_P_Fctr_Strp", "RUSLE_P_Fctr_Strp_R ot", "RUSLE_Prior_LU", "RUSLE_Res_Coef", "RUSLE_Seg_Res", "RUSLE_Setup_Prd_Seg", "RUSLE_Soil_Moisture", "RUSLE_Surf_Cover", "RUSLE_Surf_Rough", "RUSLE_Unique_Res", "Sed_Part_Distrib", "Seg_EI_Prcp", "Setup_Seg", "Soil_Comp_Surf", "Soil_Comp_Lyrs", "Storm_Types", "Climate_Daily_Wthr", "Eph_Gully_Info", "RUSLE2_Info"]
        out_inver_col = ["AnnAGNPS_ID","Cell","Climate_Station","Contour","Crop","Feedlot","Fertilizer","Mgmt_Seq","Field_Pond","Glbl_Output_Opts","Gully","Hydraulic_Geom","Impoundment","Irrigation","Landuse_Ref","Reserved","Output_Options","Pesticide","Point_Source","Reach","Runoff_Curve_Num","Simulation_Period","Soil_Actual_Surface","Strip_Crop","Tile_Drain","Mgmt_Field","Mgmt_Sched","Mgmt_Opr","Soil_Actual_Layers","Aquaculture_Pond","Aquaculture_Pond_Mg mt_Schd_A","Glbl_Err/Wrn","Soil_Init_Cond","Pest_Init_Cond","Wetland","Riparian_Buffers","RUSLE2"]
        out_sim_col = ["Cell_Components","Conversion_Units","Sht/Rill_Eros_Sed_Yld","Feedlots","Insitu_N_Inorg","Insitu_N_Org","Insitu_Residue","Insitu_OC","Insitu_P_Inorg","Insitu_P_Org","Insitu_Soil_Moist_Daily ","Irrigation","Pesticide_App","Pesticide_Insitu","Gully","Reach_Acc_Mass","Reach_Acc_Ratio","LS_Yld_All_Srcs","Reach_Ld_Nutr","Reserved","Reach_Ld_Sed","Reach_Ld_Wtr","Impound_Routing_A","Reserved","Reach_Routing_Pest","Reach_Routing","Reach_Routing_Wtr","Runoff_Curve_Num","Schd_Oprs","Soil_Part_Distrib","Pond_Release/Yield","Winter_Thermal","Reserved","USLE_Params","Baseflow","Insitu_Soil_Moist_Wsh d_Sum","Wetland_Effects","Pot_ET_Adjust","LS_Rnof_All_Srcs","Riparian_Buffers"]
        out_aa_col = ["Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "AA_Gullies(erosion)", "Reserved", "Reserved", "AA_N_Ld_Mass", "AA_N_Ld_Ratio", "AA_N_Ld_UA", "AA_N_Yld_Mass", "AA_N_Yld_Ratio", "AA_N_Yld_UA", "AA_OC_Ld_Mass", "AA_OC_Ld_Ratio", "AA_OC_Ld_UA", "AA_OC_Yld_Mass", "AA_OC_Yld_Ratio", "AA_OC_Yld_UA", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "AA_P_Ld_Mass", "AA_P_Ld_Ratio", "AA_P_Ld_UA", "AA_P_Yld_Mass", "AA_P_Yld_Ratio", "AA_P_Yld_UA", "Reserved", "Reserved", "Reserved", "AA_Sed_Eros_Mass", "AA_Sed_Eros_Ratio", "AA_Sed_Eros_UA", "AA_Sed_Ld_Mass", "AA_Sed_Ld_Ratio", "AA_Sed_Ld_UA", "AA_Sed_Yld_Mass", "AA_Sed_Yld_Ratio", "AA_Sed_Yld_UA", "AA_Wtr_Ld_Mass", "AA_Wtr_Ld_Ratio", "AA_Wtr_Ld_UA", "AA_Wtr_Yld_Mass", "AA_Wtr_Yld_Ratio", "AA_Wtr_Yld_UA"]
        out_ev_col = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
        out_tbl_col =  ["CCHE1D", "CONCEPTS_XML", "Gaging_Station_Hyd", "REMM", "Gaging_Station_Evt"]
        out_minmax_col = ["Min_Evt_Date","Max_Evt_Date","Max_Number_Evts","Min_Rnof_Evt","Min_Rnof_Cell","Min_Rnof_Outlet","Min_Subarea_ID","Max_Subarea_ID","Subarea_Units_Positn","Max_Vrfy_File_Access","Max_Vrfy_File_Bytes","Input_Units_Code"]
        dic_bc_simulation = {self.inputs.s19:annaid_col,self.inputs.s20:global_error_col,self.inputs.s21:global_ids_col,self.inputs.s22:pesticide_initial_col,self.inputs.s23:pl_calibration_col,self.inputs.s24:rcn_col,self.inputs.s25:sim_col,self.inputs.s26:soil_initial_col,self.inputs.s27:rusle2_col,self.inputs.s28:out_global_col,self.inputs.s29:out_csv_col,self.inputs.s30:out_dpp_col,self.inputs.s31:out_inver_col,self.inputs.s32:out_sim_col,self.inputs.s33:out_aa_col,self.inputs.s34:out_ev_col,self.inputs.s35:out_tbl_col,self.inputs.s36:out_minmax_col}
        self.dic_boton_columnas = {**dic_bc_watershed,**dic_bc_general,**dic_bc_climate,**dic_bc_simulation}
                        
        #Importar el archivo master
        self.inputs.pb_master.clicked.connect(self.add_master)
        
        #Se le da a los botones de Clear selection para borrar los archivos en cada seccion
        self.inputs.clear_w.clicked.connect(lambda _,b="watershed": self.delete_lines(b))
        self.inputs.clear_g.clicked.connect(lambda _,b="general": self.delete_lines(b))
        self.inputs.clear_c.clicked.connect(lambda _,b="climate": self.delete_lines(b))
        self.inputs.clear_s.clicked.connect(lambda _,b="simulation": self.delete_lines(b))
        
        #Condición para que cuando le de a change se pueda elegir otro directorio
        self.inputs.change_w.clicked.connect(lambda _,b="watershed": self.change_directory_input(b))
        self.inputs.change_g.clicked.connect(lambda _,b="general": self.change_directory_input(b))
        self.inputs.change_c.clicked.connect(lambda _,b="climate": self.change_directory_input(b))
        self.inputs.change_s.clicked.connect(lambda _,b="simulation": self.change_directory_input(b))
        
        #Botón para guardar proyecto
        self.dlg.pb_save.clicked.connect(self.save_project)
        
        #Botón para cargar el proyecto
        self.dlg.pb_load.clicked.connect(self.load_project)
        
        #Diccionario que relaciona cada linea de texto con la carpeta
        self.dic_folder = {self.inputs.l_2:self.inputs.l_1,self.inputs.l_3:self.inputs.l_1,self.inputs.l_4:self.inputs.l_1,self.inputs.l_5:self.inputs.l_1,self.inputs.l_6:self.inputs.l_1,self.inputs.l_7:self.inputs.l_1,self.inputs.l_8:self.inputs.l_1,self.inputs.l_9:self.inputs.l_1,self.inputs.l_10:self.inputs.l_1,self.inputs.l_11:self.inputs.l_1,self.inputs.l_12:self.inputs.l_1,self.inputs.l_13:self.inputs.l_1,self.inputs.l_14:self.inputs.l_1,self.inputs.l_15:self.inputs.l_1,self.inputs.l_16:self.inputs.l_1,self.inputs.l_17:self.inputs.l_1,self.inputs.l_18:self.inputs.l_1,self.inputs.l_19:self.inputs.l_1,self.inputs.l_20:self.inputs.l_1,self.inputs.l_21:self.inputs.l_1,self.inputs.l_22:self.inputs.l_1,self.inputs.l_24:self.inputs.l_23,self.inputs.l_25:self.inputs.l_23,self.inputs.l_26:self.inputs.l_23,self.inputs.l_27:self.inputs.l_23,self.inputs.l_28:self.inputs.l_23,self.inputs.l_29:self.inputs.l_23,self.inputs.l_30:self.inputs.l_23,self.inputs.l_31:self.inputs.l_23,self.inputs.l_32:self.inputs.l_23,self.inputs.l_33:self.inputs.l_23,self.inputs.l_34:self.inputs.l_23,self.inputs.l_35:self.inputs.l_23,self.inputs.l_36:self.inputs.l_23,self.inputs.l_37:self.inputs.l_23,self.inputs.l_38:self.inputs.l_23,self.inputs.l_39:self.inputs.l_23,self.inputs.l_40:self.inputs.l_23,self.inputs.l_41:self.inputs.l_23,self.inputs.l_42:self.inputs.l_23,self.inputs.l_43:self.inputs.l_23,self.inputs.l_44:self.inputs.l_23,self.inputs.l_45:self.inputs.l_23,self.inputs.l_46:self.inputs.l_23,self.inputs.l_48:self.inputs.l_47,self.inputs.l_49:self.inputs.l_47,self.inputs.l_50:self.inputs.l_47,self.inputs.l_51:self.inputs.l_47,self.inputs.l_52:self.inputs.l_47,self.inputs.l_54:self.inputs.l_53,self.inputs.l_55:self.inputs.l_53,self.inputs.l_56:self.inputs.l_53,self.inputs.l_57:self.inputs.l_53,self.inputs.l_58:self.inputs.l_53,self.inputs.l_59:self.inputs.l_53,self.inputs.l_60:self.inputs.l_53,self.inputs.l_61:self.inputs.l_53,self.inputs.l_62:self.inputs.l_53,self.inputs.l_63:self.inputs.l_53,self.inputs.l_64:self.inputs.l_53,self.inputs.l_65:self.inputs.l_53,self.inputs.l_66:self.inputs.l_53,self.inputs.l_67:self.inputs.l_53,self.inputs.l_68:self.inputs.l_53,self.inputs.l_69:self.inputs.l_53,self.inputs.l_70:self.inputs.l_53,self.inputs.l_71:self.inputs.l_53}
        
        #Poner que los inputs que genera topagnps los crea topagnps y que no es necesario decirle la ubicación
        lista = [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3,self.inputs.checkBox_4]
        for i in lista:
            i.stateChanged.connect(lambda _,b=i: self.topagnps_provided(b))
        
        #Abrir la documentación de los inptus de AnnAGNPS
        self.inputs.pb_doc.clicked.connect(self.documentation.show)
        
        #Poner los tooltips
        self.add_tooltipts()
        
        #Poner las imágenes y condiciones de la página inicial
        self.images_dialog()
        
        #Ejecutar si se da a OK
        self.dlg.pushButton_6.clicked.connect(self.ejecuciones)
        self.dlg.pushButton_4.clicked.connect(self.ejecuciones)
        
        #Cuando se cierre o ejecute el diálogo que se guarden los índices de los combobox
        self.dlg.finished.connect(self.combo_save)
        
        #Botón para respositorio de github
        self.dlg.pg_github.clicked.connect(self.url_github)
        
        #Cambiar el color de las elecciones de los outputs
        self.output_selection = {self.output.pushButton_6:"Runoff",self.output.pushButton_2:"Subtotal",self.output.pushButton_3:"Gully",self.output.pushButton_4:"Pond",self.output.pushButton_5:"Sheet & Rill",self.output.pushButton_7:"Nitrogen",self.output.pushButton_8:"Carbon",self.output.pushButton_10:"Phosphorus"}
        for i in self.output_selection.keys():
            i.clicked.connect(lambda _,b = i:self.change_color_outputs(b))
        self.data_type = "Runoff"
        #El filtro no ha sido clickado
        self.filter_clicked = 0
        self.output_exist()

        #Poner icono de búsqueda en los outputs
        self.output.pushButton_12.setIcon(QIcon(self.icon_path_search))
        self.output.pushButton_9.setIcon(QIcon(self.icon_path_search))
        
        #Seleccionar archivo DEM en los outputs
        self.output.pushButton_12.clicked.connect(lambda _,b = "AnnAGNPS":self.dem_output_file(b))
        self.output.pushButton_9.clicked.connect(lambda _,b = "TopAGNPS":self.dem_output_file(b))
        
        #Cuando se cambie la carpeta de los outputs mirar si existe el archivo necesario
        self.output.lineEdit.textChanged.connect(self.output_exist)
        
        #Poner las celdas y las fechas para los filtros
        self.output.filter_run.clicked.connect(self.identify_cells_dates)
        self.filtering = False
        
        #Añadir "All cells" a los comboboxes de los outputs
        self.output.run_cell.addItems(["All cells"])
        
        #Botones para que aparezcan outputs
        self.output.pushButton.clicked.connect(self.output_evolution)
        self.output.pushButton_15.clicked.connect(self.output_top)
        self.output.pushButton_16.clicked.connect(self.output_month)
        self.output.pushButton_17.clicked.connect(self.output_year)
        self.output.pushButton_18.clicked.connect(self.output_season)
        
        #Botón para output espacial 
        self.output.spatial_run.clicked.connect(self.spatial_output)
        
        #Botón de datos generales
        self.output.general_run.clicked.connect(self.general_output)
        
        #Variable para decir si hay error cuando se importan luego los dataframes
        self.error = False
        
        #Función para los outputs de TopAGNPS
        dic = {self.output.pushButton_11:"Cell_raster",self.output.pushButton_13:"Cell_vectorial",self.output.pushButton_14:"Boundary_raster",self.output.pushButton_19:"Boundary_vectorial",self.output.pushButton_22:"Reaches_raster",self.output.pushButton_20:"Reaches_vectorial",self.output.pushButton_21:"Accumulated",self.output.pushButton_23:"Terrain_slope",self.output.pushButton_24:"Hydraulic",self.output.pushButton_25:"Terrain_aspect",self.output.pushButton_26:"RUSLE",self.output.pushButton_27:"Longest_raster",self.output.pushButton_28:"Longest_vectorial"}
        for i in dic.keys():
            i.clicked.connect(lambda _,b = dic[i]:self.output_topagnps(b))
        
    def general_output(self):
        #Método para añadir los outputs generales al diálogo
        self.import_df_spatial()
        if self.error:
            self.error = False
            return
        #Se ponen los valores
        if self.data_type == "Runoff":
            self.output.lineEdit_6.setText(f"{round(float(self.average_total),2)} mm")
            self.output.lineEdit_7.setText(f"{round(float(self.average_anual),2)} mm")
            self.output.lineEdit_8.setText(f"{round(float(self.highest_anual[1]),2)} mm")
            self.output.lineEdit_10.setText(f"{int(self.highest_anual[0])}")
            self.output.lineEdit_9.setText(f"{round(float(self.lowest_anual[1]),2)} mm")
            self.output.lineEdit_11.setText(f"{int(self.lowest_anual[0])}")
        elif self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill" or self.data_type == "Subtotal":
            self.output.lineEdit_6.setText(f"{round(float(self.average_total),2)} Mg")
            self.output.lineEdit_7.setText(f"{round(float(self.average_anual),2)} Mg")
            self.output.lineEdit_8.setText(f"{round(float(self.highest_anual[1]),2)} Mg")
            self.output.lineEdit_10.setText(f"{int(self.highest_anual[0])}")
            self.output.lineEdit_9.setText(f"{round(float(self.lowest_anual[1]),2)} Mg")
            self.output.lineEdit_11.setText(f"{int(self.lowest_anual[0])}")
        else:
            self.output.lineEdit_6.setText(f"{round(float(self.average_total),2)} kg")
            self.output.lineEdit_7.setText(f"{round(float(self.average_anual),2)} kg")
            self.output.lineEdit_8.setText(f"{round(float(self.highest_anual[1]),2)} kg")
            self.output.lineEdit_10.setText(f"{int(self.highest_anual[0])}")
            self.output.lineEdit_9.setText(f"{round(float(self.lowest_anual[1]),2)} kg")
            self.output.lineEdit_11.setText(f"{int(self.lowest_anual[0])}")
    
    def spatial_output(self):
        #Método para poner los outputs espaciales
        #Primero se carga el dataframe
        df = self.import_df_spatial()
        if self.error:
            self.error = False
            return
        #Se pone el epsg del proyecto
        self.epsg = QgsProject.instance().crs().authid()
        #Se borran todos los archivos previos creados que se puedan 
        ficheros = os.listdir(os.path.dirname(self.output.lineEdit.text()))
        delete_files = [x for x in ficheros if x[:16]=="cell_runoff_all_" or x[:16]=="cell_runoff_cell"]
        for d in delete_files:
            try:
                os.remove(os.path.dirname(self.output.lineEdit.text())+f"\\{d}")
            except:
                pass
        #Función para importar ficheros
        def fichero(fich):
            return os.path.dirname(self.output.lineEdit.text())+f"\\{fich}"
        #Si no está el archivo AnnAGNPS_Cell_IDs.asc, entonces dar error
        if not path.exists(fichero("AnnAGNPS_Cell_IDs.asc")):
            iface.messageBar().pushMessage(f"AnnAGNPS_Cell_IDs.asc not found: AnnAGNPS_Cell_IDs.asc file must be in {os.path.dirname(self.output.lineEdit.text())}",level=Qgis.Warning, duration=10)
            return
        #Función para cambiar de coordenadas
        def change_coordinates(filename,outputname):
            input_raster = gdal.Open(fichero(filename))
            output_raster = fichero(outputname)
            warp = gdal.Warp(output_raster,input_raster,dstSRS=self.epsg)
            warp = None # Closes the files
        #Ahora se ponen los datos espaciales en QGIS
        c = 0
        while True:
            c+=1
            if not os.path.exists(fichero(f"cell_runoff_all_{c}.gpkg")) and not os.path.exists(fichero(f"cell_runoff_all_out_{c}.gpkg")): #para que luego no de error cuando se intente guardar porque ya existe el archivo
                change_coordinates("AnnAGNPS_Cell_IDs.asc","cell_1.asc")
                processing.run("grass7:r.to.vect", {'input':fichero("cell_1.asc"),
                    'type':2,'column':'value','-s':False,
                    '-v':False,'-z':False,'-b':False,'-t':False,
                    'output':fichero(f"cell_runoff_all_{c}.gpkg"),'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':False})
                break
        #Esta función es para crear una copia de archivo y que las columnas se añadan ahí
        def copiar_archivo(input_file,output):
            processing.run("native:savefeatures", 
                {'INPUT':fichero(input_file),
                'OUTPUT':fichero(output),
                'LAYER_NAME':'','DATASOURCE_OPTIONS':'','LAYER_OPTIONS':''})
        try:
            copiar_archivo(f"cell_runoff_all_{c}.gpkg",f"cell_runoff_all_out_{c}.gpkg")
        except:
            iface.messageBar().pushMessage("Some error with CRS has ocurred: Please select another CRS for the project",level=Qgis.Warning, duration=10)
            return
        if self.data_type == "Runoff":
            name_layer = "Runoff(mm)"
        elif self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
            name_layer = f"{self.data_type}_yield(Mg)"
        elif self.data_type == "Subtotal":
            name_layer = "Total_yield (Mg)"
        else:
            name_layer = f"{self.data_type}_yield(kg)"
        layer = QgsVectorLayer(fichero(f"cell_runoff_all_out_{c}.gpkg"),name_layer)
        #Borrar columnas que no son las que queremos
        columnas_borrar = [x.name() for x in layer.fields() if x.name()!="fid" and x.name()!="value" and x.name()!="Cell_ID"]
        field_index = [layer.fields().indexFromName(x) for x in columnas_borrar]
        data_provider = layer.dataProvider()
        layer.startEditing()
        data_provider.deleteAttributes(field_index)
        layer.updateFields()
        layer.commitChanges()
        
        #Cambiar el nombre de la columna value por Cell_ID
        for field in layer.fields():
            if field.name() == 'value':
                with edit(layer):
                    idx = layer.fields().indexFromName(field.name())
                    layer.renameAttribute(idx, 'Cell_ID')
        
        #Poner todas las columnas
        celdas_valores = []
        for f in layer.getFeatures():
            celdas_valores.append(f["Cell_ID"])
        def asignar_erosion(diccionario_conversion,nombre_columna):
            erosion_final=[]
            for i in range(len(celdas_valores)):
                try:
                    erosion_final.append(diccionario_conversion[celdas_valores[i]])
                except:
                    erosion_final.append(0)
            pv = layer.dataProvider()
            pv.addAttributes([QgsField(str(nombre_columna),QVariant.Double)])
            context = QgsExpressionContext()
            with edit(layer):
                contador = 0
                for f in layer.getFeatures():
                    context.setFeature(f)
                    f[str(nombre_columna)] = erosion_final[contador]
                    contador+=1
                    layer.updateFeature(f)
            #Cambiar el nombre de la columna value por Cell_ID
            for field in layer.fields():
                if field.name() == 'value':
                    with edit(layer):
                        idx = layer.fields().indexFromName(field.name())
                        layer.renameAttribute(idx, 'Cell_ID')
            return layer

        #Se pone la información de las co.umnas
        for col in df.columns:
            dic = {}
            for ind in df.index:
                dic[ind]=round(float(df[df.index == ind][col].iloc[0]),3)
            layer = asignar_erosion(dic,col)
            layer.updateFields()
        
        #Borrar las celdas que no están escogidas
        if self.cell!="All cells":
            copiar_archivo(f"cell_runoff_all_out_{c}.gpkg",f"cell_runoff_cell_out_{c}.gpkg")
            layer = QgsVectorLayer(fichero(f"cell_runoff_cell_out_{c}.gpkg"),name_layer)
            ids_delete = [f.id() for f in layer.getFeatures() if int(f["Cell_ID"])!=np.int64(self.cell)]
            layer.dataProvider().deleteFeatures(ids_delete)
        QgsProject.instance().addMapLayer(layer)
        
        #Poner etiquetas
        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = "Cell_ID"
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(15)
        label_settings.setFormat(text_format)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()
        
    def import_df_spatial(self):
        #Método para obtener el dataframe para los outputs espaciales
        #Se crean las variables con los filtros
        self.cell = self.output.run_cell.currentText()
        date_in = self.output.lineEdit_4.text()
        date_fin = self.output.lineEdit_5.text()
        try:
            date_in = datetime(int(date_in.split("/")[2]),int(date_in.split("/")[1]),int(date_in.split("/")[0]))
            date_fin = datetime(int(date_fin.split("/")[2]),int(date_fin.split("/")[1]),int(date_fin.split("/")[0]))
        except:
            iface.messageBar().pushMessage("Please select correct dates",level=Qgis.Warning, duration=10)
            self.error = True
            return
        #Se obtienen los datos ordenados
        if self.data_type == "Runoff":
            path = self.output.lineEdit.text()+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            try:
                df_raw = self.df_section_output(path,delete_second=True).iloc[2:,]
            except:
                iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                self.error = True
                return
            df = pd.DataFrame(data = {"Year": df_raw["Year"].astype(int),"Month": df_raw["Month"].astype(int),"Day": df_raw["Day"].astype(int),"Cell": df_raw["ID"].astype(int),"Runoff": df_raw["Depth"].astype(float),"RSS": df_raw["Rainfall"].astype(float) + df_raw["Snowfall"].astype(float) + df_raw["Snowmelt"].astype(float) + df_raw["Irrigation"].astype(float)})
        else:
            dic_outputs = {"Subtotal":["AnnAGNPS_EV_Sediment_yield_(mass).csv","Subtotals [Mg]"],"Gully":["AnnAGNPS_EV_Sediment_yield_(mass).csv","Subtotals [Mg]"],"Pond":["AnnAGNPS_EV_Sediment_yield_(mass).csv","Subtotals [Mg]"],"Sheet & Rill":["AnnAGNPS_EV_Sediment_yield_(mass).csv","Subtotals [Mg]"],"Nitrogen":["AnnAGNPS_EV_Nitrogen_yield_(mass).csv","Subtotal N [kg]"],"Carbon":["AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv","Subtotal C [kg]"],"Phosphorus":["AnnAGNPS_EV_Phosphorus_yield_(mass).csv","Subtotal P [kg]"]}
            path = self.output.lineEdit.text()+f"\\{dic_outputs[self.data_type][0]}"
            try:
                df_raw = self.df_section_output(path,delete_second=False)
            except:
                iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                self.error = True
                return
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill" or self.data_type == "Subtotal":
                df = pd.DataFrame(data = {"Year":[int(x) for x in df_raw["Year"]],"Month":[int(x) for x in df_raw["Month"]],"Day":[int(x) for x in df_raw["Day"]],"Cell":[str(x) for x in df_raw["Cell ID"]],"Source":[str(x) for x in df_raw["Source"]],"Runoff":[float(x) for x in df_raw[dic_outputs[self.data_type][1]]]})
            else:
               df = pd.DataFrame(data = {"Year":[int(x) for x in df_raw["Year"]],"Month":[int(x) for x in df_raw["Month"]],"Day":[int(x) for x in df_raw["Day"]],"Cell":[str(x) for x in df_raw["Cell ID"]],"Runoff":[float(x) for x in df_raw[dic_outputs[self.data_type][1]]]}) 
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
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill" or self.data_type == "Subtotal":
                df = df[df.Source == self.data_type]
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
            df_resultado['Runoff'].fillna(0, inplace=True)
            df_resultado["Cell"]=np.tile(np.unique(df.Cell), len(rango_fechas))
            df = df_resultado[["Cell","Fecha","Runoff"]]
            df.set_index('Fecha', inplace=True)
            #Se crea el dataframe final
            df = pd.DataFrame(data = {"Year":[int(x) for x in df.index.year],"Month":[int(x) for x in df.index.month],"Day":[int(x) for x in df.index.day],"Cell":[int(x) for x in df["Cell"]],"Runoff":[float(x) for x in df["Runoff"]]})
        
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
        if self.cell != "All cells":
            df = df[df.Cell==np.int64(self.cell)]
        #Aquí se filtra por fecha
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
        if self.data_type == "Runoff":
            year_average = [(x,resultado[x].sum()/len(resultado)) for x in resultado.columns]
        else:
            year_average = [(x,resultado[x].sum()) for x in resultado.columns]
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
        #Estadísticas generales
        if self.data_type == "Runoff":
            self.average_total = resultado_final.Total.sum()/len(resultado_final)
            self.average_anual = self.average_total/((date_fin-date_in).total_seconds()/(365.25*24*60*60))
            self.highest_anual = max(year_average, key=lambda x: x [1])
            self.lowest_anual= min(year_average, key=lambda x: x [1])
        else:
            self.average_total = resultado_final.Total.sum()
            self.average_anual = self.average_total/((date_fin-date_in).total_seconds()/(365.25*24*60*60))
            self.highest_anual = max(year_average, key=lambda x: x [1])
            self.lowest_anual= min(year_average, key=lambda x: x [1])
        return resultado_final

    def import_df(self,data_type):
        #Método para importar el df que se usará en los outputs
        #Dar error si no se han escogido las fechas bien
        date_in = self.output.lineEdit_4.text()
        date_fin = self.output.lineEdit_5.text()
        try:
            date_in = datetime(int(date_in.split("/")[2]),int(date_in.split("/")[1]),int(date_in.split("/")[0]))
            date_fin = datetime(int(date_fin.split("/")[2]),int(date_fin.split("/")[1]),int(date_fin.split("/")[0]))
        except:
            iface.messageBar().pushMessage("Please select correct dates",level=Qgis.Warning, duration=10)
            self.error = True
            return 
        #Primero si se ha elegido Runoff
        if data_type == "Runoff":
            #Se obtienen los datos ordenados
            path = self.output.lineEdit.text()+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            try:
                df_raw = self.df_section_output(path,delete_second=True).iloc[2:,]
            except:
                iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                self.error = True
                return
            df = pd.DataFrame(data = {"Year": df_raw["Year"].astype(int),"Month": df_raw["Month"].astype(int),"Day": df_raw["Day"].astype(int),"Cell": df_raw["ID"].astype(int),"Runoff": df_raw["Depth"].astype(float),"RSS": df_raw["Rainfall"].astype(float) + df_raw["Snowfall"].astype(float) + df_raw["Snowmelt"].astype(float) + df_raw["Irrigation"].astype(float)})
            df['Fecha'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
            #Aquí se filtran por celda y por fecha
            self.cell = self.output.run_cell.currentText()
            if self.cell!="All cells" :
                df = df[df.Cell==np.int64(self.cell)]
            #Aquí se filtra por fecha
            df = df[(df.Fecha>=date_in)&(df.Fecha<=date_fin)]
        else: #Si se ha escogido otra cosa que no sea Runoff
            #Los filtros
            self.cell = self.output.run_cell.currentText()
            #Función para importar los datos que no son Runoff
            def dataframe_creation(path,subtotal_column, erosion = False, source = None):
                df_raw = self.df_section_output(path,delete_second=False)
                if erosion:
                    df = pd.DataFrame(data = {"Year":df_raw["Year"].astype(int),"Month":df_raw["Month"].astype(int),"Day":df_raw["Day"].astype(int),"Cell":df_raw["Cell ID"].astype(str),"Source":df_raw["Source"].astype(str),"Yield":df_raw["Subtotals [Mg]"].astype(float)})
                else:
                    df = pd.DataFrame(data = {"Year":df_raw["Year"].astype(int),"Month":df_raw["Month"].astype(int),"Day":df_raw["Day"].astype(int),"Cell":df_raw["Cell ID"].astype(str),"Yield":df_raw[subtotal_column].astype(float)})
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
                if self.cell!="All cells" :
                    df = df[df.Cell==np.int64(self.cell)]
                #Se pone la fecha
                df = df.assign(Fecha=pd.to_datetime(df[['Year', 'Month', 'Day']]))
                df = df.groupby('Fecha').sum(numeric_only=True).reset_index()
                df.set_index('Fecha', inplace=True)
                df = df["Yield"]
                rango_fechas_deseado = pd.date_range(start=date_in, end=date_fin, freq='D')
                df = df.reindex(rango_fechas_deseado, fill_value=0)
                return df
            #Se ponen aquí los inputs dependiendo de lo que se haya escogido
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill" or self.data_type == "Subtotal":
                path =  self.output.lineEdit.text()+"\\AnnAGNPS_EV_Sediment_yield_(mass).csv"
                column_name = "Subtotals [Mg]"
                try:
                    df = dataframe_creation(path,column_name,erosion = True, source = self.data_type)
                except:
                    iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                    self.error = True
                    return
            if self.data_type == "Nitrogen":
                path =  self.output.lineEdit.text()+"\\AnnAGNPS_EV_Nitrogen_yield_(mass).csv"
                column_name = "Subtotal N [kg]"
                try:
                    df = dataframe_creation(path,column_name)
                except:
                    iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                    self.error = True
                    return
            if self.data_type == "Carbon":
                path =  self.output.lineEdit.text()+"\\AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv"
                column_name = "Subtotal C [kg]"
                try:
                    df = dataframe_creation(path,column_name)
                except:
                    iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                    self.error = True
                    return
            if self.data_type == "Phosphorus":
                path =  self.output.lineEdit.text()+"\\AnnAGNPS_EV_Phosphorus_yield_(mass).csv"
                column_name = "Subtotal P [kg]" 
                try:
                    df = dataframe_creation(path,column_name)
                except:
                    iface.messageBar().pushMessage("Please select a correct folder",level=Qgis.Warning, duration=10)
                    self.error = True
                    return
        return df
    
    def output_month(self):
        #Método para que aparezca por mes de lo que se esté pidiendo (escorrentía, erosión o nutrientes)
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Primero se crean los datos necesarios
        if self.data_type == "Runoff":
            df_graph = df.groupby('Fecha').mean(numeric_only=True)[["Runoff", "RSS"]]
            df_graph = df_graph.resample('M').sum()
            df_graph = df_graph.groupby(df_graph.index.month).sum()
        else:
            df_graph = df.groupby(df.index).sum(numeric_only=True)
            df_graph = df_graph.resample('M').sum()
            df_graph = df_graph.groupby(df_graph.index.month).sum()
        df_graph.index = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if self.data_type == "Runoff":
            #Se crea el gráfico
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            ax1 = ax0.twinx()
            #Se crean los dibujos
            bar0 = ax0.bar(df_graph.index, df_graph['Runoff'] ,color='tab:blue', alpha=1, label='Runoff')
            bar1=ax1.bar(df_graph.index, df_graph['RSS'] ,color='tab:red', alpha=0.8, label='Rainfall + Snowfall + Snowmelt + Irrigation')
            #Labels de los ejes
            ax0.set_xlabel("Month",size = 15,family="arial",weight = "bold",color = "black")
            ax0.set_ylabel("Runoff (mm)",size = 15,family="arial",weight = "bold",color = "black")
            ax1.set_ylabel("Rainfall + Snowfall + Snowmelt + Irrigation (mm)",size = 15,family="arial",weight = "bold",color = "black")
            #Cambiar límites de los ejes
            ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.98)
            ax1.set_ylim(ax1.get_ylim()[0],ax1.get_ylim()[1]*1.98)
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            ax1.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Invertir eje
            ax1.invert_yaxis()
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.19,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            # Agregar etiquetas de valores encima de las barras en ax0
            for rect in bar0:
                height = rect.get_height()
                formatted_height = f'{height:,.2f}'  # Aquí se aplica el separador de miles usando f-string
                ax0.annotate(formatted_height, xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', weight="bold", size=9)

            # Agregar etiquetas de valores encima de las barras en ax1
            for rect in bar1:
                height = rect.get_height()
                formatted_height = f'{height:,.2f}'  # Aquí se aplica el separador de miles usando f-string
                ax1.annotate(formatted_height, xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', weight="bold", size=9)
        else:
            #Se crea el gráfico
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            #Se crean los dibujos
            bar0 = ax0.bar(df_graph.index, df_graph ,color='tab:blue', alpha=1, label=f'{self.data_type} yield ')
            #Labels de los ejes
            ax0.set_xlabel("Month",size = 15,family="arial",weight = "bold",color = "black")
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                ax0.set_ylabel(f"{self.data_type} yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            elif self.data_type == "Subtotal":
                ax0.set_ylabel(f"Total yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            else:
                ax0.set_ylabel(f"{self.data_type} yield (kg)",size = 15,family="arial",weight = "bold",color = "black")
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            #Cambiar límites de los ejes
            ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.4)
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.02,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            # Agregar etiquetas de valores encima de las barras en ax0
            for rect in bar0:
                height = rect.get_height()
                formatted_height = f'{height:,.2f}'  # Aquí se aplica el separador de miles usando f-string
                ax0.annotate(formatted_height, xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', weight="bold", size=9)
        #Título del gráfico
        if self.cell != "All cells":
            titulo = f"Cell {self.cell}"
        else:
            titulo = "all cells"
        if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
            plt.title(f"{self.data_type} erosion yield per month in {titulo}", y=1.05, fontsize=16)
        elif self.data_type == "Subtotal":
            plt.title(f"Total erosion yield per month in {titulo}", y=1.05, fontsize=16)
        else:
            plt.title(f"{self.data_type} yield per month in {titulo}", y=1.05, fontsize=16)
        #Guardar gráfico
        plt.savefig(self.output.lineEdit.text()+f"\\Month_{self.data_type}.png",transparent=False,bbox_inches = "tight",dpi=300)
        #Abrir el gráfico 
        os.startfile(self.output.lineEdit.text()+f"\\Month_{self.data_type}.png")
        
    def output_year(self,data_type):
        #Método para que por año de lo que se esté pidiendo (escorrentía, erosión o nutrientes)
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Primero se crean los datos necesarios
        if self.data_type == "Runoff":
            df_graph = df.groupby('Fecha').mean(numeric_only=True)[["Runoff", "RSS"]]
            df_graph = df_graph.resample('Y').sum()
            df_graph = df_graph.groupby(df_graph.index.year).sum()
        else:
            df_graph = df.groupby(df.index).sum(numeric_only=True)
            df_graph = df_graph.resample('Y').sum()
            df_graph = df_graph.groupby(df_graph.index.year).sum()
        df_graph.index = [str(x) for x in df_graph.index]
        #Se crea el gráfico
        if self.data_type == "Runoff":
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            ax1 = ax0.twinx()
            #Se crean los dibujos
            bar0 = ax0.bar(df_graph.index, df_graph['Runoff'] ,color='tab:blue', alpha=1, label='Runoff')
            bar1=ax1.bar(df_graph.index, df_graph['RSS'] ,color='tab:red', alpha=0.8, label='Rainfall + Snowfall + Snowmelt + Irrigation')
            #Labels de los ejes
            ax0.set_xlabel("Year",size = 15,family="arial",weight = "bold",color = "black")
            ax0.set_ylabel("Runoff (mm)",size = 15,family="arial",weight = "bold",color = "black")
            ax1.set_ylabel("Rainfall + Snowfall + Snowmelt + Irrigation (mm)",size = 15,family="arial",weight = "bold",color = "black")
            #Cambiar límites de los ejes
            ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.98)
            ax1.set_ylim(ax1.get_ylim()[0],ax1.get_ylim()[1]*1.98)
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            ax1.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Invertir eje
            ax1.invert_yaxis()
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.19,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            # Agregar etiquetas de valores encima de las barras en ax0
            for rect in bar0:
                height = rect.get_height()
                ax0.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom',weight = "bold",size = 12)

            # Agregar etiquetas de valores encima de las barras en ax1
            for rect in bar1:
                height = rect.get_height()
                ax1.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom',weight = "bold",size = 12)
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            plt.title(f"Runoff and water inputs per year in {titulo}", y=1.05, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+"\\Year_runoff.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+"\\Year_runoff.png")
        else:
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            #Se crean los dibujos
            bar0 = ax0.bar(df_graph.index, df_graph ,color='tab:blue', alpha=1, label=f'{self.data_type} yield ')
            #Labels de los ejes
            ax0.set_xlabel("Year",size = 15,family="arial",weight = "bold",color = "black")
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                ax0.set_ylabel(f"{self.data_type} yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            elif self.data_type == "Subtotal":
                ax0.set_ylabel(f"Total yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            else:
                ax0.set_ylabel(f"{self.data_type} yield (kg)",size = 15,family="arial",weight = "bold",color = "black")
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.02,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            #Cambiar límites de los ejes
            ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.4)
            # Agregar etiquetas de valores encima de las barras en ax0
            for rect in bar0:
                height = rect.get_height()
                formatted_height = f'{height:,.2f}'  # Aquí se aplica el separador de miles usando f-string
                ax0.annotate(formatted_height, xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', weight="bold", size=9)
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                plt.title(f"{self.data_type} erosion yield per month in {titulo}", y=1.05, fontsize=16)
            elif self.data_type == "Subtotal":
                plt.title(f"Total erosion yield per month in {titulo}", y=1.05, fontsize=16)
            else:
                plt.title(f"{self.data_type} yield per month in {titulo}", y=1.05, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+f"\\Year_{self.data_type}.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+f"\\Year_{self.data_type}.png")

    def output_season(self,data_type):
        #Método para que aparezca por estación de lo que se esté pidiendo (escorrentía, erosión o nutrientes)
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Primero se crean los datos necesarios
        if self.data_type == "Runoff":
            df_graph = df.groupby('Fecha').mean(numeric_only=True)[["Runoff", "RSS"]]
        else:
            df_graph = df.groupby(df.index).sum(numeric_only=True)
        #Función para saber la estación
        def estacion(fecha):
            estaciones = {
                "1": (datetime(year=fecha.year, month=3, day=21), datetime(year=fecha.year, month=6, day=21)),
                "2": (datetime(year=fecha.year, month=6, day=21), datetime(year=fecha.year, month=9, day=21)),
                "3": (datetime(year=fecha.year, month=9, day=21), datetime(year=fecha.year, month=12, day=21))
            }
            for estacion, (inicio,fin) in estaciones.items():
                if inicio<= fecha < fin:
                    return estacion
            return "4"
        
        #Se crea el gráfico
        if self.data_type == "Runoff":
            df_graph["Estacion"] = [estacion(x) for x in df_graph.index]
            df_graph = df_graph.groupby(df_graph.Estacion).sum()
            df_graph.index = ["Spring","Summer","Autumn","Winter"]
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            ax1 = ax0.twinx()
            #Se crean los dibujos
            bar0 = ax0.bar(df_graph.index, df_graph['Runoff'] ,color='tab:blue', alpha=1, label='Runoff')
            bar1=ax1.bar(df_graph.index, df_graph['RSS'] ,color='tab:red', alpha=0.8, label='Rainfall + Snowfall + Snowmelt + Irrigation')
            #Labels de los ejes
            ax0.set_xlabel("Season",size = 15,family="arial",weight = "bold",color = "black")
            ax0.set_ylabel("Runoff (mm)",size = 15,family="arial",weight = "bold",color = "black")
            ax1.set_ylabel("Rainfall + Snowfall + Snowmelt + Irrigation (mm)",size = 15,family="arial",weight = "bold",color = "black")
            #Cambiar límites de los ejes
            ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.98)
            ax1.set_ylim(ax1.get_ylim()[0],ax1.get_ylim()[1]*1.98)
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            ax1.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Invertir eje
            ax1.invert_yaxis()
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.19,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            # Agregar etiquetas de valores encima de las barras en ax0
            for rect in bar0:
                height = rect.get_height()
                ax0.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom',weight = "bold",size = 12)

            # Agregar etiquetas de valores encima de las barras en ax1
            for rect in bar1:
                height = rect.get_height()
                ax1.annotate(f'{height:.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom',weight = "bold",size = 12)
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            plt.title(f"Runoff and water inputs per season in {titulo}", y=1.05, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+f"\\Season_{self.data_type}.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+f"\\Season_{self.data_type}.png")
        else:
            df_graph = pd.DataFrame({'Fecha': df_graph.index, 'Yield': df_graph.values})
            numeric_columns = df_graph.select_dtypes(include='number')
            df_graph["Estacion"] = [estacion(x) for x in df_graph.Fecha]
            df_graph = df_graph.groupby('Estacion')[numeric_columns.columns].sum()
            df_graph.index = ["Spring","Summer","Autumn","Winter"]
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            #Se crean los dibujos
            bar0 = ax0.bar(df_graph.index, df_graph["Yield"] ,color='tab:blue', alpha=1, label=f'{self.data_type} yield ')
            #Labels de los ejes
            ax0.set_xlabel("Season",size = 15,family="arial",weight = "bold",color = "black")
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                ax0.set_ylabel(f"{self.data_type} yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            elif self.data_type == "Subtotal":
                ax0.set_ylabel(f"Total yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            else:
                ax0.set_ylabel(f"{self.data_type} yield (kg)",size = 15,family="arial",weight = "bold",color = "black")
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.02,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            #Cambiar límites de los ejes
            ax0.set_ylim(ax0.get_ylim()[0],ax0.get_ylim()[1]*1.4)
            # Agregar etiquetas de valores encima de las barras en ax0
            for rect in bar0:
                height = rect.get_height()
                formatted_height = f'{height:,.2f}'  # Aquí se aplica el separador de miles usando f-string
                ax0.annotate(formatted_height, xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom', weight="bold", size=9)
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                plt.title(f"{self.data_type} erosion yield per month in {titulo}", y=1.05, fontsize=16)
            elif self.data_type == "Subtotal":
                plt.title(f"Total erosion yield per month in {titulo}", y=1.05, fontsize=16)
            else:
                plt.title(f"{self.data_type} yield per month in {titulo}", y=1.05, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+f"\\Season_{self.data_type}.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+f"\\Season_{self.data_type}.png")
        
    def output_top(self,data_type):
        #Método para que aparezca el top 10 días de lo que se esté pidiendo (escorrentía, erosión o nutrientes)
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Se crean los dataframes dependiendo de si se ha filtrado la celda
        if self.data_type == "Runoff":
            df_graph = df.groupby('Fecha').mean(numeric_only=True)[["Runoff", "RSS"]]
        else:
            df_graph = df.groupby(df.index).sum(numeric_only=True)
        #Se calculan los datos
        if self.data_type == "Runoff":
            if len(df_graph[df_graph['Runoff']>0])>10:
                n_top_values = 10
            else:
                n_top_values = len(df_graph[df_graph['Runoff']>0])
            top_runoff = df_graph['Runoff'].nlargest(n_top_values) 
            top_runoff_dates = top_runoff.index
            table_data = {'Date': top_runoff_dates, 'Runoff (mm)': round(top_runoff,2)}
            table_df = pd.DataFrame(table_data)
            #Se crea el grafico
            plt.rcParams["figure.figsize"] = [10, 8]
            fig, ax = plt.subplots()
            # Ajustar el formato de las fechas en el DataFrame
            table_df['Date'] = table_df['Date'].dt.strftime('%Y-%m-%d')
            table = ax.table(cellText=table_df.values, colLabels=table_df.columns, loc='center', cellLoc='center', colColours=['#f5f5f5'] * len(table_df.columns))
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 1.5)
            # Ocultar ejes x e y
            ax.axis('off')
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            plt.suptitle(f"Top 10 days with the highest runoff in {titulo} ", y=0.75, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+"\\Top_runoff.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+"\\Top_runoff.png")
        else:
            if len(df_graph[df_graph>0])>10:
                n_top_values = 10
            else:
                n_top_values = len(df_graph[df_graph>0])
            top_runoff = df_graph.nlargest(n_top_values) 
            top_runoff_dates = top_runoff.index
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                table_data = {'Date': top_runoff_dates, f'{self.data_type} erosion yield (Mg)': round(top_runoff,2)}
            elif self.data_type == "Subtotal":
                table_data = {'Date': top_runoff_dates, 'Total erosion yield (Mg)': round(top_runoff,2)}
            else:
                table_data = {'Date': top_runoff_dates, f"{self.data_type} yield (kg)": round(top_runoff,2)}
            table_df = pd.DataFrame(table_data)
            #Se crea el grafico
            plt.rcParams["figure.figsize"] = [10, 8]
            fig, ax = plt.subplots()
            # Ajustar el formato de las fechas en el DataFrame
            table_df['Date'] = table_df['Date'].dt.strftime('%Y-%m-%d')
            table_df[f"{self.data_type} yield (kg)"] = table_df[f"{self.data_type} yield (kg)"].apply(lambda x: f'{x:,.2f}')
            try:
                table = ax.table(cellText=table_df.values, colLabels=table_df.columns, loc='center', cellLoc='center', colColours=['#f5f5f5'] * len(table_df.columns))
            except:
                iface.messageBar().pushMessage("No day with value higher than 0",level=Qgis.Warning, duration=10)
                return
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 1.5)
            # Ocultar ejes x e y
            ax.axis('off')
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                plt.suptitle(f"Top 10 days with the highest {self.data_type} erosion yield in {titulo} ", y=0.75, fontsize=16)
            elif self.data_type == "Subtotal":
                plt.suptitle(f"Top 10 days with the highest total erosion yield in {titulo} ", y=0.75, fontsize=16)
            else:
                plt.suptitle(f"Top 10 days with the highest {self.data_type} yield in {titulo} ", y=0.75, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+f"\\Top_{self.data_type}.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+f"\\Top_{self.data_type}.png")
        
    def output_evolution(self,data_type):
        #Método para que aparezca la evolución de lo que se esté pidiendo (escorrentía, erosión o nutrientes)
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #SE CREA DE EVOLUCIÓN GRÁFICO
        #Se crean los dataframes dependiendo de si se ha filtrado la celda
        if self.data_type == "Runoff":
            df_graph = df.groupby('Fecha').mean(numeric_only=True)[["Runoff", "RSS"]]
            acumulado_runoff = df_graph['Runoff'].cumsum()
        else:
            df_graph = df.groupby(df.index).sum(numeric_only=True)
            acumulado_runoff = df_graph.cumsum()
        
        #Se empieza con el gráfico
        if self.data_type == "Runoff":
            #Se crean los ejes
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            ax1 = ax0.twinx()
            ax2 = ax0.twinx()
            #Se crean los dibujos
            ax0.bar(df_graph.index, df_graph['Runoff'], width =6 ,color='tab:blue', alpha=1, label='Runoff')
            ax1.bar(df_graph.index, df_graph['RSS'], width =6 ,color='tab:red', alpha=0.8, label='Rainfall + Snowfall + Snowmelt + Irrigation')
            ax2.plot(np.array(df_graph.index), np.array(acumulado_runoff) ,color="green", linestyle='--', label='Accumulated runoff')
            #Labels de los ejes
            ax0.set_xlabel("Date",size = 15,family="arial",weight = "bold",color = "black")
            ax0.set_ylabel("Runoff (mm)",size = 15,family="arial",weight = "bold",color = "black")
            ax1.set_ylabel("Rainfall + Snowfall + Snowmelt + Irrigation (mm)",size = 15,family="arial",weight = "bold",color = "black")
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
            ax2.annotate(f'{ultimo_valor_acumulado:,.2f} mm',
                         xy=(df_graph.index[-1], ultimo_valor_acumulado),
                         xytext=(-50, 10), textcoords='offset points',
                         fontsize=11, color='black', weight='bold')
            #Formato eje x
            ax0.xaxis.set_major_locator(mdates.YearLocator(base=1, month=1, day=1))
            ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax0.xaxis.set_minor_locator(mdates.MonthLocator())
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.19,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            plt.title(f"Evolution of runoff and water inputs in {titulo}", y=1.05, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+"\\Runoff_evolution.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+"\\Runoff_evolution.png")
        else:
            #Se crean los ejes
            plt.rcParams["figure.figsize"] = [10, 8]
            fig = plt.figure()
            ax0 = plt.subplot()
            ax2 = ax0.twinx()
            #Se crean los dibujos
            ax0.bar(df_graph.index, df_graph, width =6 ,color='tab:blue', alpha=1, label=f'{self.data_type} yield ')
            ax2.plot(np.array(df_graph.index), np.array(acumulado_runoff) ,color="green", linestyle='--', label='Accumulated runoff')
             #Labels de los ejes
            ax0.set_xlabel("Date",size = 15,family="arial",weight = "bold",color = "black")
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                ax0.set_ylabel(f"{self.data_type} yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
                ax2.set_ylabel(f"{self.data_type} accumulated yield (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            elif self.data_type == "Subtotal":
                ax0.set_ylabel(f"Total yield erosion (Mg)",size = 15,family="arial",weight = "bold",color = "black")
                ax2.set_ylabel("Total accumulated yield erosion (Mg)",size = 15,family="arial",weight = "bold",color = "black")
            else:
                ax0.set_ylabel(f"{self.data_type} yield (kg)",size = 15,family="arial",weight = "bold",color = "black")
                ax2.set_ylabel(f"{self.data_type} accumulated yield (kg)",size = 15,family="arial",weight = "bold",color = "black")
            #Fuente del eje
            ax0.tick_params(axis = "both",colors = "black",labelsize = 11)
            ax2.tick_params(axis = "both",colors = "black",labelsize = 11)
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            ax2.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            # Agregar una etiqueta en el último punto del acumulado
            ultimo_valor_acumulado = acumulado_runoff.iloc[-1]
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill" or self.data_type == "Subtotal":
                ax2.annotate(f'{ultimo_valor_acumulado:,.2f} Mg',
                             xy=(df_graph.index[-1], ultimo_valor_acumulado),
                             xytext=(-50, 10), textcoords='offset points',
                             fontsize=11, color='black', weight='bold')
            else:
                ax2.annotate(f'{ultimo_valor_acumulado:,.2f} kg',
                             xy=(df_graph.index[-1], ultimo_valor_acumulado),
                             xytext=(-50, 10), textcoords='offset points',
                             fontsize=11, color='black', weight='bold')
            #Formato eje x
            ax0.xaxis.set_major_locator(mdates.YearLocator(base=1, month=1, day=1))
            ax0.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            ax0.xaxis.set_minor_locator(mdates.MonthLocator())
            #Leyenda
            legend = fig.legend(bbox_to_anchor=(0.03,0.57,0.3,0.3),framealpha=0.7)
            legend.legendPatch.set_edgecolor("black")
            legend.legendPatch.set_facecolor("white")
            legend.legendPatch.set_linewidth(1)
            #Título del gráfico
            if self.cell != "All cells":
                titulo = f"Cell {self.cell}"
            else:
                titulo = "all cells"
            if self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                plt.title(f"Evolution of {self.data_type} yield erosion in {titulo}", y=1.05, fontsize=16)
            elif self.data_type == "Subtotal":
                plt.title(f"Evolution of total yield erosion in {titulo}", y=1.05, fontsize=16)
            else:
                plt.title(f"Evolution of {self.data_type} yield in {titulo}", y=1.05, fontsize=16)
            #Guardar gráfico
            plt.savefig(self.output.lineEdit.text()+f"\\Evolution_{self.data_type}.png",transparent=False,bbox_inches = "tight",dpi=300)
            #Abrir el gráfico 
            os.startfile(self.output.lineEdit.text()+f"\\Evolution_{self.data_type}.png")
                
    def output_exist(self):
        #Método para que se diga si existe el output o no
        #Se hace función para no repetir todo el rato lo mismo
        def function_output_exist(file,column,input_file):
            if path.exists(self.output.lineEdit.text()+f"\\{file}"):
                #Se cambia el icono
                path_icon = os.path.join(self.plugin_directory, "images/yes_file.svg")
                self.output.file_ex.setIcon(QIcon(path_icon))
                #Se cambia el next step
                if self.filter_clicked:
                    self.output.label_9.setText("NEXT STEP: select cells and period of time you want to study. Then select the outputs you want to show.")
                else:
                    self.output.label_9.setText("NEXT STEP: click on 'Add cells and dates' button.")
            
            else:
                #Se cambia el icono
                path_icon = os.path.join(self.plugin_directory, "images/no_file.svg")
                self.output.file_ex.setIcon(QIcon(path_icon))
                if self.output.lineEdit.text()!="":
                    self.output.label_9.setText(f"NEXT STEP: the folder you have selected does not contain the {file} file.It is necessary to make a execution where the {column} column of the {input_file} file is set to T.")
                else:
                    self.output.label_9.setText(f"NEXT STEP: select the folder in which {file} is located.")
        #Se ponen las condiciones
        if self.data_type == "Runoff":
            function_output_exist("AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv","Insitu_Soil_Moisture_Daily","OUTPUT OPTIONS DATA - SIM")
        elif self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill" or self.data_type == "Subtotal":
            function_output_exist("AnnAGNPS_EV_Sediment_yield_(mass).csv","EV_Sed_Yld_Mass","OUTPUT OPTIONS DATA – EV")
        elif self.data_type == "Nitrogen":
            function_output_exist("AnnAGNPS_EV_Nitrogen_yield_(mass).csv","EV_N_Yld_Mass","OUTPUT OPTIONS DATA – EV")
        elif self.data_type == "Carbon":
            function_output_exist("AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv","EV_OC_Yld_Mass","OUTPUT OPTIONS DATA – EV")
        elif self.data_type == "Phosphorus":
            function_output_exist("AnnAGNPS_EV_Phosphorus_yield_(mass).csv","EV_P_Yld_Mass","OUTPUT OPTIONS DATA – EV")
        
    def df_section_output(self,fichero,delete_second =False):
        #Método que se utiliza para obtener el dataframe de los resultados para crear los gráficos
        if self.data_type == "Runoff" or self.filtering:
            first_column = "Gregorian"
        else:
            first_column = "Month"
        file = open(fichero)
        csvreader = csv.reader(file)
        rows = []
        for row in csvreader:
               rows.append(row)
        lista = []
        a = 0
        for i in rows:
           try:
               if i[0]==first_column:
                   a = 1
                   lista.append(i)
               elif a ==1:
                   lista.append(i[:-1])
           except:
               continue
        if delete_second:
           lista.pop(1)
        return pd.DataFrame(columns = lista[0],data = lista[1:])
               
    def identify_cells_dates(self):
        #Método para poner celdas y fechas que contiene el archivo
        try: #Este try es para que no de error si se le da al botón de filtros cuando no existe el archivo
            #Se obtienen los datos ordenados
            path = self.output.lineEdit.text()+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            #Se importan los datos
            self.filtering = True
            df_raw = self.df_section_output(path,delete_second=True).iloc[2:,]
            self.filtering = False
            #Se ponen las celdas en el combobox
            #Primero se borran los elementos que puede haber en el combobox y luego se pone
            self.output.run_cell.clear()
            cells = [str(x) for x in np.unique(df_raw.ID)]
            cells.insert(0,"All cells")
            self.output.run_cell.addItems(cells)
            #Se ponen las fechas
            self.output.lineEdit_4.setText(f"{df_raw.Day.iloc[0]}/{df_raw.Month.iloc[0]}/{df_raw.Year.iloc[0]}")
            self.output.lineEdit_5.setText(f"{df_raw.Day.iloc[-1]}/{df_raw.Month.iloc[-1]}/{df_raw.Year.iloc[-1]}")
            #Se cambia el next step
            self.filter_clicked = 1
            self.output.label_9.setText("NEXT STEP: select cells and period of time you want to study. Then select the outputs you want to show.")
        except:
            pass

        
    def dem_output_file(self,output_type):
        #Método para seleccionar la carpeta de 
        fname = QFileDialog.getExistingDirectory(self.output, "Select folder", "C/")
        try:#este try es porque si cierras el diálogo de la carpeta para buscar archivos da error
            if output_type == "AnnAGNPS":
                if fname[0]!="":
                    self.output.lineEdit.setText(fname)
            elif output_type == "TopAGNPS":
                if fname[0]!="":
                    self.output.lineEdit_2.setText(fname)
        except:
            pass
                
    def change_color_outputs(self,button):
        #Método para cambiar el color de los labels que indican qué outpus se quiere mostrar
        button.setStyleSheet("background-color: #99ff99")
        for i in self.output_selection:
            if i!=button:
                i.setStyleSheet("background-color: #87CEEB;")
        #Se le dice al plugin cuál es la elección de output
        self.data_type = self.output_selection[button]
        #Se ejecuta el método para que se vea si existe el archivo
        self.output_exist()
        
    def path_exist(self):
        #Método para mostrar si los inputs de AnnAGNPS existen o no
        if self.border == False:
            for i in self.lines_dialog:
                    if i.text()!="" and path.exists(self.dic_folder[i].text()+"\\"+i.text()) and i.text()!="-- Provided by TopAGNPS --":
                        i.setStyleSheet("QLineEdit {border: 3px solid #00FF00; }\n QLineEdit { background-color: rgb(196, 240, 119) ; }")
                    elif i.text()!="" and not path.exists(self.dic_folder[i].text()+"\\"+i.text()) and i.text()!="-- Provided by TopAGNPS --":
                        i.setStyleSheet("QLineEdit {border: 3px solid red;}\n QLineEdit { background-color: rgb(196, 240, 119) ; }")
        if self.border == True:
            for i in self.lines_dialog:
                if i.text()!="" and i.text()!="-- Provided by TopAGNPS --":
                    i.setStyleSheet("QLineEdit { background-color: rgb(196, 240, 119) ; }")
                elif i.text()!="-- Provided by TopAGNPS --":
                    i.setStyleSheet("QLineEdit { background-color: rgb(250, 159, 160) ; }")
        if self.border == True: self.border =False #esto es para que sepa que en el plugin no están puestos los bordes
        else : self.border =True
        
    def combo_save(self):
        #Método para guardar los inputs de los combobox al cerrar el diálogo principal
        try:
            self.cdem = [self.dlg.comboBox.itemText(i) for i in range(self.dlg.comboBox.count())][self.dlg.comboBox.currentIndex()]
            self.cbuffer = [self.dlg.comboBox_2.itemText(i) for i in range(self.dlg.comboBox_2.count())][self.dlg.comboBox_2.currentIndex()]
            self.cvegetation = [self.dlg.comboBox_3.itemText(i) for i in range(self.dlg.comboBox_3.count())][self.dlg.comboBox_3.currentIndex()]
            self.csoil =[self.dlg.cbSoil.itemText(i) for i in range(self.dlg.cbSoil.count())][self.dlg.cbSoil.currentIndex()]
            self.cmangement =[self.dlg.cbMan.itemText(i) for i in range(self.dlg.cbMan.count())][self.dlg.cbMan.currentIndex()]
            self.csoilc =[self.dlg.cbColumnSoil.itemText(i) for i in range(self.dlg.cbColumnSoil.count())][self.dlg.cbColumnSoil.currentIndex()]
            self.cmanagementc =[self.dlg.cbColumnMan.itemText(i) for i in range(self.dlg.cbColumnMan.count())][self.dlg.cbColumnMan.currentIndex()]
        except:
            pass

    def images_dialog(self):
        #Método para poner las imágenes y condiciones de la página inicial
        #Crear función para poner imagenes
        def put_image(url_image,label,width):
            full_image_path = os.path.join(self.plugin_directory, url_image) 
            pixmap = QPixmap(full_image_path)
            new_width = width
            scaled_pixmap = pixmap.scaledToWidth(new_width, Qt.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
        #Upna
        put_image("images/upna.png",self.dlg.upna_label,100)
        put_image("images/upna.png",self.output.upna_label,100)
        self.dlg.upna_label.mousePressEvent  = self.url_upna
        self.output.upna_label.mousePressEvent  = self.url_upna
        #Usda
        put_image("images/usda.png",self.dlg.usda_label,100)
        put_image("images/usda.png",self.output.usda_label,100)
        self.dlg.usda_label.mousePressEvent  = self.url_usda
        self.output.usda_label.mousePressEvent  = self.url_usda
        #Símbolo plugin
        put_image("images/logo.svg",self.dlg.plugin_label,175)
        #Nombre 
        put_image("images/logo.png",self.dlg.label_7,200)
        #AnnAGNPS input
        input_icon = os.path.join(self.plugin_directory, "images/annagnps_input.svg")
        self.dlg.pb_ann.setIcon(QIcon(input_icon))
        #Modify control files
        input_icon = os.path.join(self.plugin_directory, "images/annagnps_input.svg")
        self.dlg.pbControl.setIcon(QIcon(input_icon))
        #Documentation
        documentation_icon = os.path.join(self.plugin_directory, "images/documentation.svg")
        self.inputs.pb_doc.setIcon(QIcon(documentation_icon))
        #Runoff output
        runoff = [self.output.pushButton,self.output.pushButton_15,self.output.pushButton_16,self.output.pushButton_17,self.output.pushButton_18]
        icon = os.path.join(self.plugin_directory, "images/bar_graph.svg")
        for i in runoff:
            i.setIcon(QIcon(icon)) 
        #Datos espaciales
        icon = os.path.join(self.plugin_directory, "images/spatial_graph.svg")
        self.output.spatial_run.setIcon(QIcon(icon))
        for i in [self.output.pushButton_11,self.output.pushButton_13,self.output.pushButton_14,self.output.pushButton_19,self.output.pushButton_22,self.output.pushButton_20,self.output.pushButton_21,self.output.pushButton_23,self.output.pushButton_24,self.output.pushButton_25,self.output.pushButton_26,self.output.pushButton_27,self.output.pushButton_28]:
            i.setIcon(QIcon(icon))
        
    def url_upna(self,event):
        #Método para abrir las páginas web de la upna
        webbrowser.open("https://www.unavarra.es/portada")

    def url_usda(self,event):
        #Método para abrir las páginas web de usda
        webbrowser.open("https://www.usda.gov/")
    def url_github(self,event):
        #Método para abrir el repositorio de github
        webbrowser.open("https://github.com/Inigobarbe/QGIS-AnnAGNPS")

    def topagnps_provided(self,check):
        #Método para poner si se va a usar el output de topagnps para cell, EG, reach y riparian buffer data
        dic = {self.inputs.checkBox:self.inputs.l_3,self.inputs.checkBox_2:self.inputs.l_5,self.inputs.checkBox_3:self.inputs.l_10,self.inputs.checkBox_4:self.inputs.l_41}
        if check.isChecked():
            dic[check].setText("-- Provided by TopAGNPS --")
        elif str(dic[check].text())=="-- Provided by TopAGNPS --":
            dic[check].setText("")
            
    def change_sensitivity_color(self,linea):
        if str(linea.text())!="":
            linea.setStyleSheet("QLineEdit { background-color: #CCCCCC; }")
        else:
            linea.setStyleSheet("QLineEdit { background-color: #FFFFFF; }")
        
    def overwrite_file(self):
        #Se crea el nuevo archivo y se abre
        with open(self.file_to_overwrite, mode="w", newline="") as archivo:
            writer = csv.writer(archivo)
            writer.writerow(self.dic_boton_columnas[self.boton_to_overwrite])
        os.startfile(self.file_to_overwrite)
        #Se pone en la línea de texto el nuevo archivo creado
        if os.path.isabs(self.file_to_overwrite):
            self.line_to_write.setText(os.path.split(self.file_to_overwrite)[1])
        else:
            self.line_to_write.setText(self.file_to_overwrite)
        self.overwrite.close()
        
    def not_overwrite_file(self):
        self.overwrite.close()
    
    def change_icons(self,linea):
        #Método para cambiar el icono según haya o no texto en las secciones (inputs) de AnnAGNPS.
        if linea.text()!="":
            self.inverted_dict[linea].setIcon(QIcon(self.icon_path_document))
            self.inverted_dict[linea].setToolTip(self.tr("Open document"))
        else:
            self.inverted_dict[linea].setIcon(QIcon(self.icon_path_createdocument))
            self.inverted_dict[linea].setToolTip(self.tr("Create document"))
            
    def open_file(self,boton):
        #Método para que se abra el archivo que contiene los datos de las secciones de AnnAGNPS
        if self.dic_botones[boton].text()!="":
            try:
                if os.path.isabs(self.dic_botones[boton].text()):
                    os.startfile(self.dic_botones[boton].text())
                else:
                    os.startfile(self.dic_folder[self.dic_botones[boton]].text()+"/"+self.dic_botones[boton].text())
            except:
                if self.dic_botones[boton].text()!="-- Provided by TopAGNPS --":
                    if os.path.isabs(self.dic_botones[boton].text()):
                        self.existing.label.setText(f"{str(self.dic_botones[boton].text())} does not exist")
                    else:
                        self.existing.label.setText("{} does not exist".format(self.dic_folder[self.dic_botones[boton]].text()+"/"+self.dic_botones[boton].text()))
                    self.existing.show()
        else:
            try:
                file_path = self.dic_folder[self.dic_botones[boton]].text()+"/"+self.dic_boton_archivo[boton]
                if path.exists(file_path):
                    #Esto es para que se muestre mensaje de si se quiere sobreescribir el archivo
                    self.overwrite.label.setText(f"{file_path} exist. Do you want to overwrite the file?")
                    self.file_to_overwrite = file_path
                    self.line_to_write = self.dic_botones[boton]
                    self.boton_to_overwrite = boton
                    self.overwrite.show()
                else:
                    #Se crea el nuevo archivo y se abre
                    with open(file_path, mode="w", newline="") as archivo:
                        writer = csv.writer(archivo)
                        writer.writerow(self.dic_boton_columnas[boton])
                    os.startfile(file_path)
                    #Se pone en la línea de texto el nuevo archivo creado
                    self.dic_botones[boton].setText(self.dic_boton_archivo[boton])
            except:
                pass
        
    def change_colors(self,linea):
        #Método para cambiar el color de las lineas de los inputs de AnnAGNPS según haya o no texto escrito
        if linea.text()!="":
            linea.setStyleSheet("QLineEdit { background-color: rgb(196, 240, 119) ; }")
        else:
            linea.setStyleSheet("QLineEdit { background-color: rgb(250, 159, 160) ; }")

    def setDirectory(self):
        #Método para que cuando se seleccione el DEM ya se tenga en todo el código la dirección y el epsg. También se ponen la dirección de las carpetas en el diálogo de los outputs. 
        if self.dlg.comboBox.currentIndex() >=1:
            try: #el try es para que no de error cuando se escoge una capa que no esté guardada en algún sitio
                layers = QgsProject.instance().layerTreeRoot().children()
                selectedLayerIndex = self.dlg.comboBox.currentIndex()-1
                selectedLayer = layers[selectedLayerIndex].layer()
                fichero_mdt =  selectedLayer.dataProvider().dataSourceUri()
                mdt_directory, mdt_file = os.path.split(fichero_mdt)
                self.mdt_directory = mdt_directory
                self.direccion=mdt_directory
                self.epsg = QgsProject.instance().crs().authid()
                self.files_directory()
                #Poner el nombre de la carpeta en los outputs
                self.output.lineEdit.setText(mdt_directory)
                self.output.lineEdit_2.setText(mdt_directory)
            except:
                pass
        
        
    def set_coordinates(self):
        #ESTO ES PARA LA CAPTURA DE COORDENADAS
        self.pluginIsActive = False
        self.dockwidget = None
        self.crs = QgsCoordinateReferenceSystem(self.epsg)
        self.transform = QgsCoordinateTransform()
        self.transform.setDestinationCrs(self.crs)
        if self.crs.mapUnits() == QgsUnitTypes.DistanceDegrees:
            self.userCrsDisplayPrecision = 5
        else:
            self.userCrsDisplayPrecision = 3
        self.canvasCrsDisplayPrecision = None
        self.iface.mapCanvas().destinationCrsChanged.connect(self.setSourceCrs)
        self.setSourceCrs()
        self.mapTool = Coordinate(self.iface.mapCanvas())
        self.mapTool.mouseMoved.connect(self.mouseMoved)
        self.mapTool.mouseClicked.connect(self.mouseClicked)
        self.startCapturing()
        if not self.pluginIsActive:
            self.pluginIsActive = True
            # print "** STARTING CoordinateCapture"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = CoordinateCaptureDockWidget()
                self.dockwidget.userCrsToolButton.clicked.connect(self.setCrs)
                self.dockwidget.captureButton.clicked.connect(self.startCapturing)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            # show the dockwidget
            # TODO: fix to allow choice of dock location
            #self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            #self.dockwidget.show()'''
                
    def cambios_suelo(self):
        #Función para que aparezca el nombre de las columnas al seleccionar la capa de suelos
        self.dlg.cbColumnSoil.clear()
        selectedLayerIndex = self.dlg.cbSoil.currentIndex()-1
        if selectedLayerIndex >=0:
            try:
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
                selectedLayer = layers[selectedLayerIndex]
                fields = selectedLayer.fields()
                field_names = [field.name() for field in fields]
                self.dlg.cbColumnSoil.addItems(field_names)
                self.soil_field_names = field_names
            except:
                pass
                
    def cambios_manejo(self):
        #Función para que aparezca el nombre de las columnas al seleccionar la capa de usos
        self.dlg.cbColumnMan.clear()
        selectedLayerIndex = self.dlg.cbMan.currentIndex()-1
        if selectedLayerIndex >=0:
            try:
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
                selectedLayer = layers[selectedLayerIndex]
                fields = selectedLayer.fields()
                field_names = [field.name() for field in fields]
                self.dlg.cbColumnMan.addItems(field_names)
                self.management_field_names = field_names
            except:
                pass
                
    def buffer_nombre(self):
        #Asignar en el control file de AGBUF el nombre del archivo que se ha seleccionado en el plugin como el buffer
        if self.dlg.comboBox.currentIndex()>0:
            if path.exists(self.direccion+"/AGBUF.csv"):
                layers = QgsProject.instance().layerTreeRoot().children()
                selectedLayerIndex = self.dlg.comboBox_2.currentIndex()-1
                selectedLayer = layers[selectedLayerIndex].layer()
                fichero_buffer =  selectedLayer.dataProvider().dataSourceUri()
                buffer_directory, buffer_file = os.path.split(fichero_buffer)
                control = pd.read_csv(self.direccion+"/AGBUF.csv",encoding = "ISO-8859-1",delimiter=",")
                control.iloc[0,0]=buffer_file
                control.to_csv(self.direccion+"/AGBUF.csv", index=False, float_format='%.5f')
        
    def vegetation_nombre(self):
        #Asignar en el control file de AGBUF el nombre del archivo que se ha seleccionado en el plugin como el vegetation   
        if self.dlg.comboBox.currentIndex()>0:
            if path.exists(self.direccion+"/AGBUF.csv"):
                layers = QgsProject.instance().layerTreeRoot().children()
                selectedLayerIndex = self.dlg.comboBox_3.currentIndex()-1
                selectedLayer = layers[selectedLayerIndex].layer()
                fichero_vegetation =  selectedLayer.dataProvider().dataSourceUri()
                vegetation_directory, vegetation_file = os.path.split(fichero_vegetation)
                control = pd.read_csv(self.direccion+"/AGBUF.csv",encoding = "ISO-8859-1",delimiter=",")
                control.iloc[0,1]=vegetation_file
                control.to_csv(self.direccion+"/AGBUF.csv", index=False, float_format='%.5f')

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions: 
            self.iface.removePluginVectorMenu(
                self.tr(u'&QAnnAGNPS'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        #Este es la función general del botón principal
        
        #Inicializar variables
        self.segunda_ronda = False #cuando se elige la coordenada automáticamente se ejecuta TOPAGNPS dos veces. Esto es para que se sepa si es la primera o segunda ronda.
        self.end_sensitivity = 0 #si es igual a 1 entonces se para el análisis de sensibilidad

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = EphemeralGullyDialog()
        # Fetch the currently loaded layers
        layers = QgsProject.instance().layerTreeRoot().children()
        self.layers = layers
        
        #Hacer que el desplegable de las columnas se quede vacío después de las ejecuciones anteriores
        self.dlg.comboBox.clear()
        self.dlg.cbSoil.clear()
        self.dlg.cbMan.clear()
        self.dlg.cbColumnSoil.clear()
        self.dlg.cbColumnMan.clear()
        self.dlg.comboBox_2.clear()
        self.dlg.comboBox_3.clear()

        #Añadir al desplegable las capas que están en el proyecto
        project_layers = [layer.name() for layer in layers]
        project_layers.insert(0,"")
        try:
            self.dlg.comboBox.addItems(project_layers)
        except:
            pass
        try:
            self.dlg.cbSoil.addItems(project_layers)
        except:
            pass
        self.dlg.cbMan.addItems(project_layers)
        self.dlg.comboBox_2.addItems(project_layers)
        self.dlg.comboBox_3.addItems(project_layers)
        
        #Ahora se añaden los índices de los comboboxes previamente escogidos
        def set_index_combo(combo, attribute_name):
            try:
                saved = getattr(self, attribute_name)
                indice = [combo.itemText(i) for i in range(combo.count())].index(saved)
                combo.setCurrentIndex(indice)
            except (AttributeError, ValueError):
                pass
        set_index_combo(self.dlg.comboBox,"cdem")
        set_index_combo(self.dlg.comboBox_2,"cbuffer")
        set_index_combo(self.dlg.comboBox_3,"cvegetation")
        set_index_combo(self.dlg.cbSoil,"csoil")
        set_index_combo(self.dlg.cbMan,"cmangement")
        set_index_combo(self.dlg.cbColumnSoil,"csoilc")
        set_index_combo(self.dlg.cbColumnMan,"cmanagementc")

        #Mostrar el diálogo principal
        self.dlg.show()
        self.ejecucion_condicion=0
        
    def ejecuciones(self):
        #Método para las ejecuciones
        self.dlg.close()
        #Ejecutar
        self.ejecucion_completa()
          
    def ejecucion_completa(self):
        #Esta función es en donde se ejecuta el modelo
        #Primero se establece la variable que contiene las capas del proyecto
        layers = QgsProject.instance().layerTreeRoot().children()
        
        #Establecer directorio de DEM y EPSG del proyecto
        selectedLayerIndex = self.dlg.comboBox.currentIndex()-1
        selectedLayer = layers[selectedLayerIndex].layer()
        fichero_mdt =  selectedLayer.dataProvider().dataSourceUri()
        epsg = QgsProject.instance().crs().authid()
        self.epsg = epsg
        #Establecer el fichero de suelo escogido en el plugin
        selectedLayerIndex = self.dlg.cbSoil.currentIndex()-1
        selectedLayer = layers[selectedLayerIndex].layer()
        fichero_soil =  selectedLayer.dataProvider().dataSourceUri()
        soil_directory, fichero_soil = os.path.split(fichero_soil)
        #Establecer el fichero de manejo escogido en el plugin
        selectedLayerIndex = self.dlg.cbMan.currentIndex()-1
        selectedLayer = layers[selectedLayerIndex].layer()
        fichero_manag =  selectedLayer.dataProvider().dataSourceUri()
        manag_directory, fichero_manag = os.path.split(fichero_manag)
        #Se cambia de directorio al mismo en el que se encuentra el mdt y se establece el directorio donde están los ejecutables
        mdt_directory, mdt_file = os.path.split(fichero_mdt)
        executable_directory  = self.plugin_dir+"\\Executables"
        os.chdir(mdt_directory)
        #EJECUCIÓN DE TOPAGNPS
        if self.dlg.cbTop.isChecked():
            #Si el input output_global Glbl_All_V3_sim no se pone en T no se obtiene el archivo que se necesita para calcular la erosión por cárcavas efímeras (AnnAGNPS_SIM_Ephemeral_Gully_Erosion.csv) y por lo tanto no se puede hacer el análisis de sensibilidad
            #Esto se hace primero porque la dirección puede estar dada con el nombre del archivo o en dirección completa
            if os.path.isabs(r"{}".format(str(self.inputs.l_63.text()))):
                file_glbl = str(self.inputs.l_63.text())
            else:
                file_glbl = str(self.inputs.l_53.text()) + "/" + str(self.inputs.l_63.text())
            #Función para que se le diga el nombre del archivo y te devuelva la dirección completa
            def fichero(nombre):
                return mdt_directory+"\\"+nombre
            
            #Si el mdt elegido en el plugin es distinto al que sale en TOPAGNPS.csv entonces cambiar el nombre del de TOPAGNPS.csv al elegido por en el plugin
            if not os.path.exists(self.direccion+"\\TOPAGNPS.CSV"):
                iface.messageBar().pushMessage("Error Input data", "Control file of TopAGNPS, TOPAGNPS.CSV, not found" ,level=Qgis.Warning, duration=10)
                return
            topagnps_control_file = pd.read_csv(self.direccion+"\\TOPAGNPS.CSV",encoding = "ISO-8859-1",delimiter=",")
            if type(topagnps_control_file["FILENAME"].iloc[0])!=str:
                iface.messageBar().pushMessage("Error Input data", "Please select a correct FILENAME in TOPAGNPS.CSV" ,level=Qgis.Warning, duration=10)
                return
            if topagnps_control_file["FILENAME"].iloc[0] != mdt_file:
                processing.run("gdal:translate", 
                    {'INPUT':fichero(mdt_file),
                    'TARGET_CRS':epsg,'NODATA':None,'COPY_SUBDATASETS':False,
                    'OPTIONS':'','EXTRA':'','DATA_TYPE':0,'OUTPUT':topagnps_control_file["FILENAME"].iloc[0]})
            
            #EJECUCIÓN DE TOPAGNPS            
            def main():
                f = open(executable_directory+"\\"+"EjecutarTopagnps.bat","w+")
                linea_uno = "CD {}".format(mdt_directory)
                linea_dos = r"CALL {}\TopAGNPS_v6.00.a.020_release_64-bit.exe".format(executable_directory)
                f.write("{} \n".format(linea_uno))
                f.write("{} \n".format(linea_dos))
                f.close()
            main()
            subprocess.call(executable_directory+"\\"+"EjecutarTopagnps.bat")
            
            #Cuando se eligen coordenadas automáticamente con el plugin primero se ejecuta Topagnps y da error (se ejecuta la primera para poner el reaches en QGIS) osea que no queremos que python salte si hay error en la primera ronda. Queremos que salte python cuando hay error y si se ha seleccionado que no se elige automaticamente. O sino cuando hay error y se ha elegido automáticamente pero la segunda ejecución de Topagnps da error. 
            if os.path.isfile("TOPAGNPS_err.CSV") and os.path.getsize("TOPAGNPS_err.CSV")>0 and (not self.dlg.checkBox_2.isChecked() or self.segunda_ronda):
                self.end_sensitivity = 1
                error = pd.read_csv(fichero("TOPAGNPS_err.CSV"),encoding = "ISO-8859-1",delimiter=",")
                iface.messageBar().pushMessage("Error TOPAGNPS", error.columns[3],level=Qgis.Warning, duration=10)
                #Se abre el archivo de errores
                try:
                    os.startfile(self.direccion+"\\TopAGNPS_err.csv")
                except:
                    pass
                #Este return es para parar el codigo
                return
            
            #Función para cambiar de coordenadas
            def change_coordinates(filename,outputname):
                        input_raster = gdal.Open(fichero(filename))
                        output_raster = fichero(outputname)
                        warp = gdal.Warp(output_raster,input_raster,dstSRS=epsg)
                        warp = None # Closes the files
            #Esto es para cambiar las coordenadas del outlet en TOPAGNPS.csv. Para ello se tiene que estar en primera ronda y se tiene que haber elegido la opción de escoger el outlet automáticamente. 
            if self.dlg.checkBox_2.isChecked() and not self.segunda_ronda:
                if self.ejecucion_condicion == 0:
                    change_coordinates("AnnAGNPS_Reach_IDs.asc","AnnAGNPS_Reach_IDs_epsg.asc")
                    layer = QgsRasterLayer(fichero("AnnAGNPS_Reach_IDs_epsg.asc"),"reaches")
                    QgsProject.instance().addMapLayer(layer)
                    self.set_coordinates()
            self.segunda_ronda = False
            #VALORES DEL TAMAÑO DE PIXEL
            layer = QgsRasterLayer(topagnps_control_file["FILENAME"].iloc[0],"dednm")
            pixelSizeX = round(layer.rasterUnitsPerPixelX(),2)
            pixelSizeY = round(layer.rasterUnitsPerPixelY(),2)
            
            #ASIGNAR LOS VALORES DE SUELO Y MANEJO A AnnAGNPS_Cell_Data_Section.csv
            #A esta función le das la capa de celdas y la que se superpone (tipo de suelo o uso) y devuelve el diccionario en el que se muestra a cada celda que valor (de suelo o de uso) le corresponde
            def aplicar(fichero_celdas,fichero_superponer, columna_tipo,numero):
                numero = str(numero) #esto es porque no deja sobreescribir y tengo que crear otra capa por cada ejecución de sensibilidad
                fichero_cell = fichero_celdas
                fichero_suelo = fichero_superponer
                #Esta función devuelve un diccionario en donde a cada suelo/uso se le asigna un numero entero y luego en la capa (de suelos o uso) a cada suelo/uso se le añade el valor del diccionario
                def create_fid(file_layer):
                    layer = QgsVectorLayer(fichero(file_layer),"estadistica")
                    tipos_suelo = []
                    for f in layer.getFeatures():
                        tipos_suelo.append(f[columna_tipo])
                    tipos_suelo = np.unique(tipos_suelo)
                    tipos_suelo_dic = {tipos_suelo[x]:x+1 for x in range(len(tipos_suelo))}

                    pv = layer.dataProvider()
                    pv.addAttributes([QgsField("id_prueba",QVariant.Int)])
                    context = QgsExpressionContext()
                    with edit(layer):
                        for f in layer.getFeatures():
                            context.setFeature(f)
                            f["id_prueba"] = tipos_suelo_dic[f[columna_tipo]]
                            layer.updateFeature(f)
                    layer.updateFields()
                    return tipos_suelo_dic

                #Pasar de shp a gpkg
                processing.run("native:reprojectlayer", 
                    {'INPUT':fichero(fichero_suelo),
                    'TARGET_CRS':QgsCoordinateReferenceSystem(epsg),
                    'OPERATION':'+proj=noop','OUTPUT':fichero("suelos{}.gpkg".format(numero))})
                #Reproyectar celdas al epsg del proyecto
                processing.run("gdal:warpreproject", 
                    {'INPUT':fichero(fichero_cell),
                    'SOURCE_CRS':None,'TARGET_CRS':QgsCoordinateReferenceSystem('{}'.format(epsg)),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,
                    'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OUTPUT':fichero("cell_1{}.asc".format(numero))})
                #Con esto se tiene el diccionario que te asigna para cada suelo/uso un valor numérico
                dic_conv = create_fid("suelos{}.gpkg".format(numero))
                #Rasterizar la capa de suelos
                processing.run("gdal:rasterize", 
                    {'INPUT':fichero("suelos{}.gpkg".format(numero)),
                    'FIELD':'id_prueba','BURN':0,'USE_Z':False,'UNITS':1,'WIDTH':pixelSizeX,
                    'HEIGHT':pixelSizeY,'EXTENT':None,'NODATA':0,'OPTIONS':'','DATA_TYPE':4,'INIT':None,
                    'INVERT':False,'EXTRA':'','OUTPUT':fichero("suelo_ras.tif")})
                #Vectorizar la capa de celdas
                processing.run("grass7:r.to.vect", {'input':fichero("cell_1{}.asc".format(numero)),
                    'type':2,'column':'value','-s':False,
                    '-v':False,'-z':False,'-b':False,'-t':False,
                    'output':fichero("cell{}.gpkg".format(numero)),'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':False})
                #Corregir geometrías porque luego sino en unión da error
                processing.run("native:fixgeometries", 
                    {'INPUT':fichero("cell{}.gpkg".format(numero)),
                    'OUTPUT':fichero("cell_cor{}.gpkg".format(numero))})    
                #Se unen las capas de celdas de celdas con las de suelo/uso
                processing.run("native:union", 
                {'INPUT':fichero("cell_cor{}.gpkg".format(numero)),
                'OVERLAY':fichero("suelos{}.gpkg".format(numero)),
                'OVERLAY_FIELDS_PREFIX':'','OUTPUT':fichero("union_capas{}.gpkg".format(numero))})
                #Esta función es para crear una columna en una capa vectorial según la expresión que le pongas
                def create_attribute(layer_name, expresion,nombre_columna):
                    layer = QgsVectorLayer(fichero(layer_name),"union")
                    pv = layer.dataProvider()
                    pv.addAttributes([QgsField(nombre_columna,QVariant.Double)])
                    expression1 = QgsExpression(expresion)
                    context = QgsExpressionContext()
                    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
                    with edit(layer):
                        for f in layer.getFeatures():
                            context.setFeature(f)
                            f[nombre_columna] = expression1.evaluate(context)
                            layer.updateFeature(f)
                    layer.updateFields()
                #De la capa de unión creada se calcula el área para cada zona
                create_attribute("union_capas{}.gpkg".format(numero),"$area","area_zona")
                
                #Ahora se ve qué área de suelo/uso es la mayor para cada celda y esa será la que se escoja
                layer = QgsVectorLayer(fichero("union_capas{}.gpkg".format(numero)),"union")
                tres_valores = []
                valores_unicos_celdas = []
                valores_unicos_suelos=[]
                for f in layer.getFeatures():
                            tres_valores.append((f["value"],f["id_prueba"],f["area_zona"]))
                            valores_unicos_celdas.append(f["value"])
                            valores_unicos_suelos.append(f["id_prueba"])
                valores_unicos_celdas = list(np.unique(valores_unicos_celdas))
                valores_unicos_suelos=list(np.unique(valores_unicos_suelos))
                valores_unicos_celdas=[x for x in valores_unicos_celdas if type(x)==float]
                valores_unicos_suelos=[x for x in valores_unicos_suelos if type(x)==np.int32 or type(x)==int ]
                lista_final = []
                for i in valores_unicos_celdas:
                    lista_maximos = []
                    for x in valores_unicos_suelos:
                        try:
                            suma = sum([f[2] for f in tres_valores if f[0] == i and f[1] == x])
                            lista_maximos.append((x,suma))
                        except:
                            pass
                    lista_final.append((i,max(lista_maximos,key = lambda p:p[1])[0]))
                diccionario_conversion = {x[0]:x[1] for x in lista_final}
                dic_conv = {v: k for k, v in dic_conv.items()}
                diccionario_final = {list(diccionario_conversion.keys())[x]:dic_conv[diccionario_conversion[list(diccionario_conversion.keys())[x]]] for x in range(len(diccionario_conversion))}
                return diccionario_final,dic_conv
            #Se importa el data frame en el que se muestran las celdas 
            annagnps_cell_data = pd.read_csv("AnnAGNPS_Cell_Data_Section.csv",encoding = "ISO-8859-1",delimiter=",")
            #Dar error si no se ha elegido ni capa de suelos ni se ha puesto un suelo único
            if str(self.dlg.lineEdit.text())=="":
                if self.dlg.cbSoil.currentIndex()==0:
                    iface.messageBar().pushMessage("Error with soil layer","There isn't any soil information to use",level=Qgis.Warning, duration=10)
                    return
                #Se aplica el suelo al fichero de cells
                try:
                    suelos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",fichero_soil,self.soil_field_names[self.dlg.cbColumnSoil.currentIndex()],1)
                except:
                    iface.messageBar().pushMessage("Error with soil layer","Soil layer has to be saved in the same folder as the DEM. Also the DEM and the soil layer have to overlap.",level=Qgis.Warning, duration=20)
                    return
                annagnps_cell_data["Soil_ID"] = [suelos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
                annagnps_cell_data.to_csv('AnnAGNPS_Cell_Data_Section.csv', index=False, float_format='%.5f')
                #Se aplica el suelo al fichero de cárcavas efímeras, si existe el archivo AnnAGNPS_Ephemeral_Gully_Data_Section.csv
                if path.exists(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv")):
                    summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                    def create_layer():
                        layer = QgsVectorLayer("Point?crs={}".format(self.epsg),"PEG_Points","memory")
                        layer.dataProvider().addAttributes([QgsField("id",QVariant.String)])
                        layer.updateFields()
                        features = []
                        for i in range(len(summary)):
                            feature = QgsFeature()
                            feature.setFields(layer.fields())
                            x = summary.X.iloc[i]
                            y = summary.Y.iloc[i]
                            pt = QgsPointXY(x,y)
                            geom = QgsGeometry.fromPointXY(pt)
                            feature.setGeometry(geom)
                            feature.setAttribute(0,summary.GULLY_ID.iloc[i])
                            features.append(feature)
                        layer.dataProvider().addFeatures(features)
                        return layer
                    summary_layer = create_layer()
                    sampling = processing.run("native:rastersampling", 
                        {'INPUT':summary_layer,
                        'RASTERCOPY':fichero("suelo_ras.tif"),
                        'COLUMN_PREFIX':'SAMPLE_','OUTPUT':'TEMPORARY_OUTPUT'})
                    capa = sampling["OUTPUT"]
                    dic_eg = {f["id"].split(" ")[0]:f["SAMPLE_1"] for f in capa.getFeatures()}
                    
                    annagnps_eg_data = pd.read_csv(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv"),encoding = "ISO-8859-1",delimiter=",")
                    suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                    try:
                        annagnps_eg_data["Soil_ID"]= [dic_conv[x] for x in suelos_eg]
                    except:
                        iface.messageBar().pushMessage("Error soil map","The soil type layer may not cover the full extent of the watershed",level=Qgis.Warning, duration=10)
                        return 
                    annagnps_eg_data.to_csv(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv"), index=False, float_format='%.5f')
                
            #Dar error si no se ha elegido ni capa de usos ni se ha puesto un uso único
            if str(self.dlg.lineEdit_2.text())=="":
                if self.dlg.cbMan.currentIndex()==0:
                        iface.messageBar().pushMessage("Error with soil management","There isn't any management information to use",level=Qgis.Warning, duration=10)
                        return 
                try:
                    manejos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",fichero_manag,self.management_field_names[self.dlg.cbColumnMan.currentIndex()],2)
                except:
                    iface.messageBar().pushMessage("Error with soil use layer","Soil use layer has to be saved in the same folder as the DEM. Also the DEM and the soil use layer have to overlap.",level=Qgis.Warning, duration=20)
                    return
                annagnps_cell_data["Mgmt_Field_ID"] = [manejos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
                annagnps_cell_data.to_csv('AnnAGNPS_Cell_Data_Section.csv', index=False, float_format='%.5f')
                #Se aplica el uso al fichero de cárcavas efímeras
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg),"PEG_Points","memory")
                    layer.dataProvider().addAttributes([QgsField("id",QVariant.String)])
                    layer.updateFields()
                    features = []
                    for i in range(len(summary)):
                        feature = QgsFeature()
                        feature.setFields(layer.fields())
                        x = summary.X.iloc[i]
                        y = summary.Y.iloc[i]
                        pt = QgsPointXY(x,y)
                        geom = QgsGeometry.fromPointXY(pt)
                        feature.setGeometry(geom)
                        feature.setAttribute(0,summary.GULLY_ID.iloc[i])
                        features.append(feature)
                    layer.dataProvider().addFeatures(features)
                    return layer
                summary_layer = create_layer()
                sampling = processing.run("native:rastersampling", 
                    {'INPUT':summary_layer,
                    'RASTERCOPY':fichero("suelo_ras.tif"),
                    'COLUMN_PREFIX':'SAMPLE_','OUTPUT':'TEMPORARY_OUTPUT'})
                capa = sampling["OUTPUT"]
                dic_eg = {f["id"].split(" ")[0]:f["SAMPLE_1"] for f in capa.getFeatures()}
                annagnps_eg_data = pd.read_csv(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv"),encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                annagnps_eg_data["Mgmt_Field_ID"]= [dic_conv[x] for x in suelos_eg]
                #Esto se hace porque cuando se asigna el suelo y su uso, las celdas de cada EG estan en formato float "5f" con cinco decimales, y el número de celdas son valores enteros
                def float_to_str(column):
                    lista = []
                    for i in annagnps_eg_data[column]:
                        try:
                            lista.append(str(int(i)))
                        except:
                            lista.append("")
                    annagnps_eg_data[column] = lista
                #Primero para la columna de celdas
                float_to_str("Cell_ID")
                #Ahora para la columna de reaches
                float_to_str("Reach_ID")
                annagnps_eg_data.to_csv(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv"), index=False, float_format='%.5f')
                
            #Si se ha puesto un suelo único entonces se añade a todas las celdas
            if str(self.dlg.lineEdit.text())!="":
                annagnps_cell_data["Soil_ID"] =str(self.dlg.lineEdit.text())
                annagnps_cell_data.to_csv('AnnAGNPS_Cell_Data_Section.csv', index=False, float_format='%.5f')
            #Si se ha puesto un uso único entonces se añade a todas las celdas
            if str(self.dlg.lineEdit_2.text())!="":
                annagnps_cell_data["Mgmt_Field_ID"]=str(self.dlg.lineEdit_2.text())
                annagnps_cell_data.to_csv('AnnAGNPS_Cell_Data_Section.csv', index=False, float_format='%.5f')
            
            #Mensaje de éxito si se ha ejecutado TOPAGNPS con éxito si no se ha escogido ejecutar AnnAGNPS
            if not self.dlg.cbAnn.isChecked() and ((not self.dlg.checkBox_2.isChecked() and self.ejecucion_condicion == 0)or (self.dlg.checkBox_2.isChecked() and self.ejecucion_condicion == 1)):
                self.iface.messageBar().pushMessage("Success", "Succes in the modeling ",level=Qgis.Success, duration=5)
            #Mensaje para que selecciones las coordenadas
            if not self.dlg.cbAnn.isChecked() and self.dlg.checkBox_2.isChecked() and self.ejecucion_condicion == 0:
                self.iface.messageBar().pushMessage("Coordinate selection", "Please move the mouse to the outlet and click on it",level=Qgis.Info, duration=10)
            
        #EJECUCIÓN DE ANNAGNPS
        if (self.dlg.cbAnn.isChecked() and not self.segunda_ronda and (self.ejecucion_condicion==1 or not self.dlg.checkBox_2.isChecked())):
            #CREACIÓN DE LA CARPETA QUE CONTENDRÁ LOS INPUTS DE ANNAGNPS
            directory = "INPUTS"
            parent_dir = mdt_directory
            path_file = os.path.join(parent_dir, directory)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass

            #CREACIÓN DE LAS SUBCARPETAS EN DONDE SE ORGANIZARÁN LOS INPUTS
            carpetas = ["simulation","general","watershed","climate"]
            parent_dir = mdt_directory +"\\" + directory
            try:
                for c in carpetas: 
                    path_file = os.path.join(parent_dir, c)
                    mode = 0o666
                    os.mkdir(path_file, mode)
            except:
                pass

            #CONCRETAR EL NOMBRE DE LOS INPUTS PARA ANNAGNPS. Obtenidos de Input_Specifications pero mejor sacarlo del input editor
            #WATERSHED
            aquaculture_pond_data= r"{}".format(str(self.inputs.l_2.text())) # el r"{}".format se pone porque si es una dirección completa luego no se puede reconocer si es una dirección completa o no
            cell_data= r"{}".format(str(self.inputs.l_3.text()))
            classic_gully= r"{}".format(str(self.inputs.l_4.text()))
            ephemeral_gully= r"{}".format(str(self.inputs.l_5.text()))
            feedlot_data= r"{}".format(str(self.inputs.l_6.text()))
            field_pond_data= r"{}".format(str(self.inputs.l_7.text()))
            impoundment_data= r"{}".format(str(self.inputs.l_8.text()))
            point_source= r"{}".format(str(self.inputs.l_9.text()))
            reach_data= r"{}".format(str(self.inputs.l_10.text()))
            ricewq_data = r"{}".format(str(self.inputs.l_11.text()))
            watershed_data = r"{}".format(str(self.inputs.l_12.text()))
            wetland_data= r"{}".format(str(self.inputs.l_13.text()))
            output_options_cell = r"{}".format(str(self.inputs.l_14.text()))
            output_options_feedlot = r"{}".format(str(self.inputs.l_15.text()))
            output_options_field = r"{}".format(str(self.inputs.l_16.text()))
            output_options_classic_gully = r"{}".format(str(self.inputs.l_17.text()))
            output_options_ephemeral_gully = r"{}".format(str(self.inputs.l_18.text()))
            output_options_impoundment = r"{}".format(str(self.inputs.l_19.text()))
            output_options_point_source = r"{}".format(str(self.inputs.l_20.text()))
            output_options_reach = r"{}".format(str(self.inputs.l_21.text()))
            output_options_wetland = r"{}".format(str(self.inputs.l_22.text()))

            #GENERAL
            aquaculture_schedule_data= r"{}".format(str(self.inputs.l_24.text()))
            contour_data= r"{}".format(str(self.inputs.l_25.text()))
            crop_data= r"{}".format(str(self.inputs.l_26.text()))
            crop_growth = r"{}".format(str(self.inputs.l_27.text()))
            feedlot_management= r"{}".format(str(self.inputs.l_28.text()))
            fertilizer_application= r"{}".format(str(self.inputs.l_29.text()))
            fertilizer_reference= r"{}".format(str(self.inputs.l_30.text()))
            geology_data= r"{}".format(str(self.inputs.l_31.text()))
            hydraulic_geometry= r"{}".format(str(self.inputs.l_32.text()))
            irrigation_application= r"{}".format(str(self.inputs.l_33.text()))
            management_field= r"{}".format(str(self.inputs.l_34.text()))
            management_operation= r"{}".format(str(self.inputs.l_35.text()))
            management_schedule_data= r"{}".format(str(self.inputs.l_36.text()))
            non_crop= r"{}".format(str(self.inputs.l_37.text()))
            pesticide_application= r"{}".format(str(self.inputs.l_38.text()))
            pesticide_reference= r"{}".format(str(self.inputs.l_39.text()))
            reach_nutrient= r"{}".format(str(self.inputs.l_40.text()))
            riparian_buffer= r"{}".format(str(self.inputs.l_41.text()))
            runoff_curve= r"{}".format(str(self.inputs.l_42.text()))
            soil_data= r"{}".format(str(self.inputs.l_43.text()))
            soil_layer_data = r"{}".format(str(self.inputs.l_44.text()))
            strip_crop= r"{}".format(str(self.inputs.l_45.text()))
            tile_drain= r"{}".format(str(self.inputs.l_46.text()))

            #CLIMATE
            climate_data_station = r"{}".format(str(self.inputs.l_48.text()))
            climate_data_daily = r"{}".format(str(self.inputs.l_49.text()))
            EI_pct_data = r"{}".format(str(self.inputs.l_50.text()))
            storm_type_rfd = r"{}".format(str(self.inputs.l_51.text()))
            storm_type_updrc = r"{}".format(str(self.inputs.l_52.text()))

            #SIMULATION
            annagnps_id = r"{}".format(str(self.inputs.l_54.text()))
            global_error = r"{}".format(str(self.inputs.l_55.text()))
            global_id = r"{}".format(str(self.inputs.l_56.text()))
            pesticide_initial= r"{}".format(str(self.inputs.l_57.text()))
            pl_calibration = r"{}".format(str(self.inputs.l_58.text()))
            rcn_calibration = r"{}".format(str(self.inputs.l_59.text()))
            simulation_period_data=r"{}".format(str(self.inputs.l_60.text()))
            soil_initial_conditions = r"{}".format(str(self.inputs.l_61.text()))
            rusle2_data= r"{}".format(str(self.inputs.l_62.text()))
            output_global = r"{}".format(str(self.inputs.l_63.text()))
            output_options_csv = r"{}".format(str(self.inputs.l_64.text()))
            output_options_dpp = r"{}".format(str(self.inputs.l_65.text()))
            output_options_npt = r"{}".format(str(self.inputs.l_66.text()))
            output_options_sim = r"{}".format(str(self.inputs.l_67.text()))
            output_options_aa= r"{}".format(str(self.inputs.l_68.text()))
            output_options_ev = r"{}".format(str(self.inputs.l_69.text()))
            output_options_tbl = r"{}".format(str(self.inputs.l_70.text()))
            output_options_mn = r"{}".format(str(self.inputs.l_71.text()))

            #METER ARCHIVOS EN CARPETAS DE INPUTS CORRESPONDIENTES. Completar cuales van a cada carpeta con el input editor.
            #Primero se asigna la dirección, si es que se ha elegido la opción de que se obtengan de la ejecución de TopAGNPS
            checks_list= [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3,self.inputs.checkBox_4]
            sections_list = [cell_data,ephemeral_gully,reach_data,riparian_buffer]
            names_list = ["AnnAGNPS_Cell_Data_Section.csv","AnnAGNPS_Ephemeral_Gully_Data_Section.csv","AnnAGNPS_Reach_Data_Section.csv","AnnAGNPS_Riparian_Buffer_Data_Section_AgBuf.csv"]
            for i in range(len(checks_list)):
                if checks_list[i].isChecked():
                    sections_list[i]=self.direccion+"\\"+names_list[i]
            cell_data,ephemeral_gully,reach_data,riparian_buffer = sections_list
            #Función para que se le diga el nombre del archivo y te devuelva la dirección completa, en este caso para los inputs que usará AnnAGNPS
            def fichero_input(file_name,direct):
                if os.path.isabs(file_name):
                    return os.path.dirname(file_name)+"/"+ directory + "/" +direct+"/"+os.path.basename(file_name)
                else:
                    return mdt_directory+"/"+ directory + "/" + direct + "/" +file_name
            
            #Listas de los nombres de archivos para cada tipo de input. Se elminan aquellos que no han sido escogidos ("")
            #Clima
            climate_files = [EI_pct_data,climate_data_daily,climate_data_station,storm_type_rfd,storm_type_updrc]
            climate_files = [x for x in climate_files if x !=""]
            #General
            general_files = [crop_data,crop_growth,fertilizer_application,fertilizer_reference,hydraulic_geometry,management_field,
                             management_operation,management_schedule_data,non_crop,riparian_buffer,runoff_curve,soil_data,soil_layer_data,
                             strip_crop,tile_drain,aquaculture_schedule_data,contour_data,feedlot_management,geology_data,
                             irrigation_application,pesticide_application,pesticide_reference,reach_nutrient,
                             ]
            general_files = [x for x in general_files if x !=""]
            #Simulation
            simulation_files = [annagnps_id,global_id,simulation_period_data,output_global,output_options_aa,output_options_tbl,
                                global_error,pesticide_initial,pl_calibration,rcn_calibration,soil_initial_conditions,output_options_csv,
                                output_options_dpp,output_options_npt, output_options_sim,output_options_mn,rusle2_data,output_options_ev]
            simulation_files = [x for x in simulation_files if x !=""]
            #Watershed
            watershed_files = [cell_data,ephemeral_gully,reach_data,watershed_data,wetland_data,aquaculture_pond_data,
                               classic_gully,feedlot_data,field_pond_data,impoundment_data,
                               point_source,output_options_cell,output_options_feedlot,output_options_field,
                               output_options_classic_gully,output_options_ephemeral_gully,output_options_impoundment,
                               output_options_point_source,output_options_reach,output_options_wetland,ricewq_data]
            watershed_files = [x for x in watershed_files if x !=""]
            #Lista de listas
            tipes_of_files = [climate_files,general_files,simulation_files,watershed_files]
            
            #Bucle para mover los inputs desde donde se encontraba el arcivo mdt a las carpetas necesarias
            #Función para tener la dirección completa dependiendo de la carpeta en la que se encuentra o de si está la dirección completa puesta
            def origin_direction(input_path, section):
                if os.path.isabs(input_path):
                    return input_path
                else:
                    if section == "watershed":
                        return self.inputs.l_1.text()+"/"+input_path
                    elif section == "general":
                        return self.inputs.l_23.text()+"/"+input_path
                    elif section == "climate":
                        return self.inputs.l_47.text()+"/"+input_path
                    elif section == "simulation":
                        return self.inputs.l_53.text()+"/"+input_path
            #Bucle para mover los archivos inputs de AnnAGNPS
            for t in tipes_of_files:
                for f in t:
                    try:
                        if t == climate_files and origin_direction(f,"climate")!=fichero_input(f,"climate"):#esta última condición es porque si no hay que mover el archivo, da error
                            shutil.copyfile(origin_direction(f,"climate"),fichero_input(f,"climate"))
                    except:
                        iface.messageBar().pushMessage("Error AnnAGNPS","{} file not found".format(origin_direction(f,"climate")),level=Qgis.Warning, duration=10)
                        return
                    try:
                        if t == general_files and origin_direction(f,"general")!= fichero_input(f,"general"):
                           shutil.copyfile(origin_direction(f,"general"),fichero_input(f,"general"))
                    except:
                        iface.messageBar().pushMessage("Error AnnAGNPS","{} file not found".format(origin_direction(f,"general")),level=Qgis.Warning, duration=10)
                        return
                    try:
                        if t == simulation_files and origin_direction(f,"simulation")!=fichero_input(f,"simulation"):
                           shutil.copyfile(origin_direction(f,"simulation"),fichero_input(f,"simulation"))
                    except:
                        iface.messageBar().pushMessage("Error AnnAGNPS","{} file not found".format(origin_direction(f,"simulation")),level=Qgis.Warning, duration=10)
                        return
                    try:
                        if t == watershed_files and origin_direction(f,"watershed")!=fichero_input(f,"watershed"):
                            shutil.copyfile(origin_direction(f,"watershed"),fichero_input(f,"watershed"))
                    except:
                        iface.messageBar().pushMessage("Error AnnAGNPS","{} file not found".format(origin_direction(f,"watershed")),level=Qgis.Warning, duration=10)
                        return
                        
            #CREACIÓN DEL ARCHIVO annagnps_master.csv
            def fichero_master(nombre):
                try:
                    if nombre in climate_files:
                        directory = "climate"
                    if nombre in general_files:
                        directory = "general"
                    if nombre in simulation_files:
                        directory = "simulation"
                    if nombre in watershed_files:
                        directory = "watershed"
                    if not os.path.isabs(nombre):
                        return ".\\"+ directory + "\\" + nombre
                    if os.path.isabs(nombre):
                        return ".\\"+ directory + "\\" + os.path.basename(nombre)
                except:
                    return nombre 
            master_dict = {"AnnAGNPS ID":annagnps_id,"Aquaculture Pond Data":aquaculture_pond_data,
                           "Aquaculture Schedule Data":aquaculture_schedule_data,"Cell Data":cell_data,"Classic Gully Data":classic_gully,
                           "Contour Data":contour_data,"Crop Data":crop_data,"Crop Growth Data":crop_growth,
                           "Ephemeral Gully Data":ephemeral_gully,"Feedlot Data":feedlot_data,"Feedlot Management Data":feedlot_management,
                           "Fertilizer Application Data":fertilizer_application,"Fertilizer Reference Data":fertilizer_reference,
                           "Field Pond Data":field_pond_data,"Geology Data":geology_data,
                           "Global Error and Warning Limits Data":global_error,"Global IDs Factors and Flags Data":global_id,
                           "Hydraulic Geometry Data":hydraulic_geometry,"Impoundment Data":impoundment_data,
                           "Irrigation Application Data":irrigation_application,"Management Field Data":management_field,
                           "Management Operation Data":management_operation,"Management Schedule Data":management_schedule_data,
                           "Non-Crop Data":non_crop,
                           "Pesticide Application Data":pesticide_application,"Pesticide Initial Conditions Data":pesticide_initial,
                           "Pesticide Reference Data":pesticide_reference,"PL Calibration Data":pl_calibration,
                           "Point Source Data":point_source,"RCN Calibration Data":rcn_calibration,"Reach Data":reach_data,
                           "Reach Nutrient Half-life Data":reach_nutrient,"Runoff Curve Number Data":runoff_curve,
                           "Simulation Period Data":simulation_period_data,"Soil Data":soil_data,"Soil Layer Data":soil_layer_data,
                           "Soil Initial Conditions Data":soil_initial_conditions,"Strip Crop Data":strip_crop,
                           "Tile Drain Data":tile_drain,"Watershed Data":watershed_data,"EI Pct Data":EI_pct_data,
                           "STORM TYPE DATA - RFD":storm_type_rfd,"STORM TYPE DATA - UPDRC":storm_type_updrc,
                           "Output Options - Global":output_global,"Output Options - AA":output_options_aa, "Output Options - EV":output_options_ev,
                           "Output Options - CSV":output_options_csv,"Output Options - DPP":output_options_dpp,
                           "Output Options - NPT":output_options_npt,"Output Options - SIM":output_options_sim,
                           "Output Options - TBL":output_options_tbl,"Output Options - MN/MX":output_options_mn,
                           "Output Options - Cell":output_options_cell,"Output Options - Feedlot":output_options_feedlot,
                           "Output Options - Field Pond":output_options_field,
                           "Output Options - Classic Gully":output_options_classic_gully,
                           "Output Options - Ephemeral Gully":output_options_ephemeral_gully,
                           "Output Options - Impoundment":output_options_impoundment,
                           "Output Options - Point Source":output_options_point_source,
                           "Output Options - Reach":output_options_reach,
                           "Output Options - Wetland":output_options_wetland,
                           "CLIMATE DATA - STATION":climate_data_station,
                           "CLIMATE DATA - DAILY":climate_data_daily,"Wetland Data":wetland_data,"Riparian Buffer Data":riparian_buffer,
                           "RUSLE2 Data":rusle2_data,"RiceWQ Data":ricewq_data}
            data_section = [list(master_dict)[x] for x in range(len(master_dict)) if master_dict[list(master_dict)[x]] !=""]
            file_name = [fichero_master(master_dict[x]) for x in data_section]
            master = pd.DataFrame(data = {"Data Section ID":data_section,"File Name":file_name})
            master.to_csv(mdt_directory + "\\" +directory + "\\" + "annagnps_master.csv", encoding='utf-8', index=False)
            
            #MOVER EL EJECUTABLE DE ANNAGNPS Y EL ANNAGNPS.FIL (CREO QUE ES EL CONTROL FILE DE ANNAGNPS) A LA CARPETA DE INPUTS 
            shutil.copyfile(executable_directory + "\\" +"AnnAGNPS.fil" ,mdt_directory + "\\"+directory+ "\\" +"AnnAGNPS.fil")

            #EJECUCIÓN DE ANNAGNPS
            os.chdir(mdt_directory+"\\"+directory)
            def execute_bat():
               def main():
                   f = open(executable_directory+"\\"+"EjecutarAnnAGNPS.bat","w+")
                   linea_uno = "CD {}".format(mdt_directory+"\\"+directory)
                   linea_dos = r"CALL {}\AnnAGNPS_v6.00.r.058_release_64-bit.exe".format(executable_directory)
                   f.write("{} \n".format(linea_uno))
                   f.write("{} \n".format(linea_dos))
                   f.close()
               main()
            execute_bat()
            subprocess.call(executable_directory+"\\"+"EjecutarAnnAGNPS.bat")
            
            #PONER MENSAJE DE ERROR SI ANNAGNPS FUNCIONA MAL
            time.sleep(1)
            if path.exists("AnnAGNPS_LOG_Error.csv"):
                if os.stat("AnnAGNPS_LOG_Error.csv").st_size>0:
                    text = open("AnnAGNPS_LOG_Error.csv", "r")
                    text = ''.join([i for i in text]) 
                    text = text.replace("\"", "/") 
                    texto = text.splitlines()
                    try:
                        txt = texto[2].split(",")[-1]
                    except:
                        pass
                    iface.messageBar().pushMessage("Error AnnAGNPS",txt,level=Qgis.Warning, duration=10)
                    self.end_sensitivity = 1
                    #Se abre el archivo de errores
                    try:
                        os.startfile(self.direccion+"\\INPUTS\\"+"AnnAGNPS_LOG_Error.csv")
                    except:
                        pass
                    #Este return es para parar el codigo
                    return 
            
            #EJECUCIÓN DEL OUTPUT_TABLES
            time.sleep(1)
            shutil.copyfile(executable_directory + "\\" +"STEAD.fil" ,mdt_directory + "\\"+directory + "\\" +"STEAD.fil")
            os.chdir(mdt_directory+"\\"+directory)
            subprocess.Popen(executable_directory + "\\" +"STEAD.exe")
            os.chdir(mdt_directory)
            
            #MENSAJE DE ÉXITO
            self.iface.messageBar().pushMessage("Success", "Succes in execution ",level=Qgis.Success, duration=5)
                  
    def startCapturing(self):
        self.iface.mapCanvas().setMapTool(self.mapTool)
        
    def setSourceCrs(self):
        self.transform.setSourceCrs(self.iface.mapCanvas().mapSettings().destinationCrs())
        if self.iface.mapCanvas().mapSettings().destinationCrs().mapUnits() == QgsUnitTypes.DistanceDegrees:
            self.canvasCrsDisplayPrecision = 5
        else:
            self.canvasCrsDisplayPrecision = 3
            
    def mouseMoved(self, point: QgsPointXY):
        a = 0
        #self.update(point)

    def mouseClicked(self, point: QgsPointXY):
        self.update(point)
        
    def setCrs(self):
        selector = QgsProjectionSelectionDialog(self.iface.mainWindow())
        selector.setCrs(self.crs)
        if selector.exec():
            self.crs = selector.crs()
            self.transform.setDestinationCrs(self.crs)
            if self.crs.mapUnits() == QgsUnitTypes.DistanceDegrees:
                self.userCrsDisplayPrecision = 5
            else:
                self.userCrsDisplayPrecision = 3
                
    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING CoordinateCapture"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

        self.mapTool.deactivate()
        
    def update(self, point: QgsPointXY):
        def fichero(nombre):
            return self.mdt_directory +"\\"+nombre
        userCrsPoint = self.transform.transform(point)
        self.dockwidget.userCrsEdit.setText('{0:.{2}f},{1:.{2}f}'.format(userCrsPoint.x(),
                                                                         userCrsPoint.y(),
                                                                         self.userCrsDisplayPrecision))
        self.dockwidget.canvasCrsEdit.setText('{0:.{2}f},{1:.{2}f}'.format(point.x(),
                                                                        point.y(),
                                                                        self.canvasCrsDisplayPrecision))
        coordenada_puntos = '{0:.{2}f},{1:.{2}f}'.format(userCrsPoint.x(),
                                                                         userCrsPoint.y(),
                                                                         self.userCrsDisplayPrecision)
        topagnps_control_file = pd.read_csv(fichero("TOPAGNPS.csv"),encoding = "ISO-8859-1",delimiter=",")
        topagnps_control_file["FORMAT"].iloc[0] = 0
        topagnps_control_file["OUTFORMAT"].iloc[0] = 1
        topagnps_control_file["OUTROW"].iloc[0] =coordenada_puntos.split(",")[1]
        topagnps_control_file["OUTCOL"].iloc[0] = coordenada_puntos.split(",")[0]
        topagnps_control_file.to_csv(fichero("TOPAGNPS.csv"), index=False, float_format='%.5f')
        self.continuar = 1
        self.segunda_ronda = True
        self.ejecucion_condicion = 1
        
        #Después de haber clicado en la coordenada ejecutar de nuevo esta vez sin pedir coordenadas
        self.ejecucion_completa()
        
        #Lo que sigue aquí lo he hecho porque no sé como hacer para que se desactive la función de update y siga pidiendo coordenadas. Creo que esto lo puse porque aunque se ejecutaba todo bien, el cursor seguía en formato de pedir coordenadas, y creo que si clicabas se volvia a ejecutar otra vez. 
        class PrintClickedPoint(QgsMapToolEmitPoint):
            def __init__(self, canvas):
                self.canvas = canvas
                QgsMapToolEmitPoint.__init__(self, self.canvas)
            def canvasPressEvent( self, e ):
                point = self.toMapCoordinates(self.canvas.mouseLastXY())
                point = list(point)
                print (point)
                self.punto = point
            def canvasReleaseEvent( self ,e):
                iface.mapCanvas().unsetMapTool( self )    
        canvas_clicked = PrintClickedPoint( iface.mapCanvas() )
        iface.mapCanvas().setMapTool( canvas_clicked )
        
    def create_control_file_topagnps(self):
        #Función para que cuando se le de al botón de aceptar en el control file de topagnps se cree el control file TOPAGNPS.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"FILENAME":[self.ctopagnps.lineEdit_7.text()],"FORMAT":[0],
                                    "DEMPROC":[self.ctopagnps.lineEdit_5.text()],"OUTFORMAT":[self.ctopagnps.lineEdit_14.text()],
                                    "OUTROW":[self.ctopagnps.lineEdit_22.text()],"OUTCOL":[self.ctopagnps.lineEdit_15.text()],
                                    "CSA":[self.ctopagnps.lineEdit_3.text()],"MSCL":[self.ctopagnps.lineEdit_10.text()],
                                    "UTME":[self.ctopagnps.lineEdit_19.text()],"UTMN":[self.ctopagnps.lineEdit_20.text()],
                                    "ROWS":[self.ctopagnps.lineEdit_18.text()],"COLS":[self.ctopagnps.lineEdit_2.text()],
                                    "CELLSIZE":[self.ctopagnps.lineEdit.text()],"NODATA":[self.ctopagnps.lineEdit_11.text()],
                                    "OUTSNAP":[self.ctopagnps.lineEdit_17.text()],"DNMCNT":[self.ctopagnps.lineEdit_6.text()],
                                    "DEMEDGE":[self.ctopagnps.lineEdit_4.text()],"VERBOSE":[self.ctopagnps.lineEdit_21.text()],
                                    "KEEPFILES":[self.ctopagnps.lineEdit_9.text()],"OPTIMIZE":[self.ctopagnps.lineEdit_12.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"TOPAGNPS.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the topagnps control file first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        self.ctopagnps.close()
        
    def create_control_file_peg(self):
        #Función para que cuando se le de al botón de aceptar en el control file de peg se cree el control file PEG.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"Input":[self.cpeg.lineEdit.text()],"CTI_value":[self.cpeg.lineEdit_2.text()],
                                    "Accum_pct":[self.cpeg.lineEdit_3.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"PEG.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the PEG control file first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        self.cpeg.close()
        
    def create_control_file_agbuf(self):
        #Función para que cuando se le de al botón de aceptar en el control file de agbuf se cree el control file Agbuf.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"Buffer":[self.cagbuf.lineEdit.text()],"Vegetation":[self.cagbuf.lineEdit_2.text()],
                                    "Forest":[self.cagbuf.lineEdit_3.text()],"Grass":[self.cagbuf.lineEdit_4.text()],
                                    "C_Threshold":[self.cagbuf.lineEdit_5.text()],"R_Threshold":[self.cagbuf.lineEdit_6.text()],
                                    "Units":[self.cagbuf.lineEdit_7.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"AgBuf.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the AGBUF control file first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        self.cagbuf.close()
        
    def create_control_file_agwet(self):
        #Función para que cuando se le de al botón de aceptar en el control file de agwet se cree el control file Agwet.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"FILENAME":[self.cagwet.lineEdit.text()],"BREACH_BARRIER":[self.cagwet.lineEdit_18.text()],
                                    "BARRIER_HEIGHT_OPTION":[self.cagwet.lineEdit_17.text()],"BARRIER_HEIGHT":[self.cagwet.lineEdit_11.text()],
                                    "BARRIER_HEIGHT_INCREMENT":[self.cagwet.lineEdit_12.text()],"BARRIER_HEIGHT_MAX":[self.cagwet.lineEdit_14.text()],
                                    "WETLAND_ID_OPTION":[self.cagwet.lineEdit_21.text()],"EROSION_INDEX_OPTION":[self.cagwet.lineEdit_20.text()],
                                    "EROSION_INDEX_THRESHOLD":[self.cagwet.lineEdit_8.text()],"DA_THRESHOLD":[self.cagwet.lineEdit_9.text()],
                                    "WI_THRESHOLD":[self.cagwet.lineEdit_7.text()],"MIN_WETLAND_RATIO":[self.cagwet.lineEdit_13.text()],
                                    "MAX_WETLAND_RATIO":[self.cagwet.lineEdit_10.text()],"BUFFER_WIDTH":[self.cagwet.lineEdit_15.text()],
                                    "BUFFER_EXTENT_OPTION":[self.cagwet.lineEdit_19.text()],"BUFFER_IDS_FILENAME":[self.cagwet.lineEdit_2.text()],
                                    "BUFFER_VEG_FILENAME":[self.cagwet.lineEdit_3.text()],"BUFFER_ZONE_FILENAME":[self.cagwet.lineEdit_4.text()],
                                    "ASC_PATH":[self.cagwet.lineEdit_5.text()],"CSV_PATH":[self.cagwet.lineEdit_6.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"AgWet.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the AGWET control file first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        self.cagwet.close()
        
    def create_control_file_concepts(self):
        #Función para que cuando se le de al botón de aceptar en el control file de concepts se cree el control file CONCEPTS.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"UPSTREAM_REACH_ID":[self.cconcepts.lineEdit.text()],"DOWNSTREAM_REACH_ID":[self.cconcepts.lineEdit_2.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"CONCEPTS.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the CONCEPTS control file first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        self.cconcepts.close()
        
    def create_control_file_pothole(self):
        #Función para que cuando se le de al botón de aceptar en el control file de pothole se cree el control file POTHOLE.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"POTHOLE_OPTION":[self.cpothole.lineEdit.text()],"POTHOLE_SURFACE_AREA":[self.cpothole.lineEdit_2.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"POTHOLE.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the POTHOLE control file first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        self.cpothole.close()
        
    def create_control_file_rasfor(self):
        #Función para que cuando se le de al botón de aceptar en el control file de rasfor se cree el control file rasfor.inp con los datos que se han puesto
        generate_program = int(self.crasfor.checkBox.isChecked())
        if self.crasfor.checkBox_2.isChecked():
            output_format=0
        if self.crasfor.checkBox_3.isChecked():
            output_format=1
        if self.crasfor.checkBox_5.isChecked():
            output_format=2
        if self.crasfor.checkBox_4.isChecked():
            output_format=3
        try:
            output_format+1
        except:
            iface.messageBar().pushMessage("Select Output Format Option", "please choose among the four output format options",level=Qgis.Warning, duration=10)
            return
        #Inputs que se cogen de lo que haya elegido el usuario
        input_dem = int(self.crasfor.checkBox_6.isChecked())
        initial= int(self.crasfor.checkBox_19.isChecked())
        depression = int(self.crasfor.checkBox_18.isChecked())
        relief_m = int(self.crasfor.checkBox_15.isChecked())
        flow_v= int(self.crasfor.checkBox_20.isChecked())
        flow_p=int(self.crasfor.checkBox_11.isChecked())
        indeterminate = int(self.crasfor.checkBox_13.isChecked())
        upstream=int(self.crasfor.checkBox_7.isChecked())
        spatially_v=int(self.crasfor.checkBox_12.isChecked())
        raster_CSA=int(self.crasfor.checkBox_10.isChecked())
        raster_MSCL=int(self.crasfor.checkBox_16.isChecked())
        drainage_ch=int(self.crasfor.checkBox_14.isChecked())
        watershed_b=int(self.crasfor.checkBox_9.isChecked())
        watershed_d=int(self.crasfor.checkBox_8.isChecked())
        subwatershed_a=int(self.crasfor.checkBox_17.isChecked())
        depression_flat=int(self.crasfor.checkBox_24.isChecked())
        equal_e=int(self.crasfor.checkBox_32.isChecked())
        flow_v=int(self.crasfor.checkBox_31.isChecked())
        terrain_a=int(self.crasfor.checkBox_33.isChecked())
        flow_v=int(self.crasfor.checkBox_26.isChecked())
        hydraulic_s=int(self.crasfor.checkBox_29.isChecked())
        terrain_s=int(self.crasfor.checkBox_23.isChecked())
        enhanc=int(self.crasfor.checkBox_27.isChecked())
        aggregat_boundary=int(self.crasfor.checkBox_35.isChecked())
        aggregated_area=int(self.crasfor.checkBox_28.isChecked())
        subwatershed_b=int(self.crasfor.checkBox_21.isChecked())
        flow_p_nearest=int(self.crasfor.checkBox_34.isChecked())
        flow_p_watershed=int(self.crasfor.checkBox_22.isChecked())
        flow_p_elevation=int(self.crasfor.checkBox_30.isChecked())
        flow_p_elevation_drop=int(self.crasfor.checkBox_25.isChecked())
        #Se obtiene el texto de un archivo rasfor (un ejemplo) para luego añadirle los valores que se han escogido en el plugin
        fichero = open(self.plugin_dir+r"\Documentos\rasfor.inp","r+")
        texto = fichero.read()
        fichero.close()
        #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
        lista_parametros = [generate_program,output_format,input_dem ,initial,depression ,relief_m ,flow_v,flow_p,indeterminate ,upstream,spatially_v,raster_CSA,raster_MSCL,drainage_ch,watershed_b,watershed_d,subwatershed_a,depression_flat,equal_e,flow_v,terrain_a,flow_v,hydraulic_s,terrain_s,enhanc,aggregat_boundary,aggregated_area,subwatershed_b,flow_p_nearest,flow_p_watershed,flow_p_elevation,flow_p_elevation_drop]
        lista = [3191,3059,3884, 4136,4311, 4514,4566,4627,4697,4761,4833,4893,4954,5024,5082,5137,5195,5487,5549,5609,5670,5729,5786,5846,5903,5979,6049,6114,6186,6259,6337,6416]
        texto_nuevo = texto
        for i in range(len(lista_parametros)):
            texto_nuevo = texto_nuevo[0:lista[i]]+str(lista_parametros[i])+texto_nuevo[lista[i]+1:]
        try:
            f = open(self.direccion+"\\"+"rasfor.inp","w+")
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the RASFOR data first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        f.write(texto_nuevo)
        f.close()
        self.crasfor.close()
        
    def create_control_file_raspro(self):
        #Función para que cuando se le de al botón de aceptar en el control file de raspro se cree el control file raspro.inp con los datos que se han puesto
        #Inputs
        program_r = int(self.craspro.checkBox.isChecked())
        process_n=int(self.craspro.checkBox_2.isChecked())
        process_e = int(self.craspro.checkBox_3.isChecked())
        compute_l= int(self.craspro.checkBox_4.isChecked())
        compute_f = int(self.craspro.checkBox_5.isChecked())
        elevation_b = str(self.craspro.lineEdit.text())
        #Se obtiene el texto de un archivo raspro (un ejemplo) para luego añadirle los valores que se han escogido en el plugin
        fichero = open(self.plugin_dir+r"\Documentos\raspro.inp","r+")
        texto = fichero.read()
        fichero.close()
        #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
        lista_parametros = [program_r,process_n,process_e,elevation_b,compute_l,compute_f]
        lista = [515, 840, 1051, 1054,1271+len(str(elevation_b))-1, 1405+len(str(elevation_b))-1]
        texto_nuevo = texto
        for i in range(len(lista_parametros)):
            texto_nuevo = texto_nuevo[0:lista[i]]+str(lista_parametros[i])+texto_nuevo[lista[i]+1:]
        try:
            f = open(self.direccion+"\\"+"raspro.inp","w+")
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the RASPRO data first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        f.write(texto_nuevo)
        f.close()
        self.craspro.close()
        
    def create_control_file_dednm(self):
        #Función para que cuando se le de al botón de aceptar en el control file de dednm se cree el control file dednm.inp con los datos que se han puesto
        #Inputs
        try:
            utm_zone = int(self.dednm.lineEdit.text())
            utm_e = int(self.dednm.lineEdit_2.text())
            utm_n = int(self.dednm.lineEdit_3.text())
            dem_r = int(self.dednm.lineEdit_4.text())
            dem_c=int(self.dednm.lineEdit_5.text())
            min_e=float(self.dednm.lineEdit_6.text())
            max_e=float(self.dednm.lineEdit_7.text())
            indet_el =float(self.dednm.lineEdit_8.text())
            dem_res=float(self.dednm.lineEdit_9.text())
            dem_or=int(self.dednm.lineEdit_10.text())
            out_row=int(self.dednm.lineEdit_11.text())
            out_col=int(self.dednm.lineEdit_16.text())
            dem_proc=1
            dem_smooth=1 #siempre estará en uno
            passes= int(self.dednm.lineEdit_12.text())
            center=int(self.dednm.lineEdit_13.text())
            cross=int(self.dednm.lineEdit_15.text())
            diagonal=int(self.dednm.lineEdit_14.text())
            perform_raster=int(self.dednm.checkBox.isChecked())
            if self.dednm.radioButton.isChecked():
                partial=1
            if self.dednm.radioButton_2.isChecked():
                partial=2
            if self.dednm.radioButton_3.isChecked():
                partial=3
            csa=int(self.dednm.lineEdit_17.text())
            mscl=int(self.dednm.lineEdit_18.text())
            #Depression
            if self.dednm.radioButton_4.isChecked():
                depression=1
            if self.dednm.radioButton_5.isChecked():
                depression=2
            if self.dednm.radioButton_6.isChecked():
                depression=3
            #Calibration options
            if self.dednm.radioButton_7.isChecked():
                cal_options=1
            if self.dednm.radioButton_8.isChecked():
                cal_options=2
            if self.dednm.radioButton_9.isChecked():
                cal_options=3
            if self.dednm.radioButton_10.isChecked():
                cal_options=4
            if self.dednm.radioButton_11.isChecked():
                cal_options=5
            progr_rep=int(self.dednm.checkBox_4.isChecked())
            inp_data=int(self.dednm.checkBox_5.isChecked())
            drainage_area=int(self.dednm.checkBox_6.isChecked())
            subcatchment_area=int(self.dednm.checkBox_7.isChecked())
            subcatchment_window=int(self.dednm.checkBox_8.isChecked())
        except:
            iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning, duration=10)
            return 
        #Se obteiene el texto de un archivo rasfor (un ejemplo) para luego añadirle los valores que se han escogido en el plugin
        fichero = open(self.plugin_dir+"\Documentos\dednm.inp","r+")
        texto = fichero.read()
        fichero.close()
        #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
        try:
            lista_parametros = [utm_zone,utm_e,utm_n,dem_r,dem_c,min_e,max_e,indet_el,dem_res,dem_or,out_row,out_col,dem_proc,dem_smooth,passes,center,cross,diagonal,perform_raster,partial,csa,mscl,depression,cal_options,progr_rep,inp_data,drainage_area,subcatchment_area,subcatchment_window]
        except:
            iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning, duration=10)
            return 
        lista = [1101, 1377, 1657, 1871, 2088, 2249, 2411, 2765, 2879, 3258, 3632, 4012, 4480, 4817, 5096, 5346, 5830, 5834, 5838, 6202, 6740, 7506, 10873, 11034, 11419, 11498, 11568, 11639, 11714]
        texto_nuevo = texto
        contador = 0
        for i in range(len(lista_parametros)):
            texto_nuevo = texto_nuevo[0:lista[i]+contador]+str(lista_parametros[i])+texto_nuevo[lista[i]+contador+1:]
            contador += len(str(lista_parametros[i]))-1
        try:
            f = open(self.direccion+"\\"+"dednm.inp","w+")
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the DEDNM data first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        f.write(texto_nuevo)
        f.close()
        self.dednm.close()
    
    def create_control_file_agflow(self):
        #Función para que cuando se le de al botón de aceptar en el control file de agflow se cree el control file dednm.inp con los datos que se han puesto
        #Función para pasar de 1 a T y de 0 a F
        def funcion_t(numero):
            if numero==1:
                return "T"
            elif numero ==0:
                return "F"
        #Inputs
        try:
            slope= int(self.agflow.lineEdit_4.text())
            maxim_d=float(self.agflow.lineEdit_5.text())
            maxim_pl=float(self.agflow.lineEdit_6.text())
            maxim_ps=float(self.agflow.lineEdit_7.text())
            use=funcion_t(int(self.agflow.checkBox.isChecked()))
            write=funcion_t(int(self.agflow.checkBox_2.isChecked()))
            arc=funcion_t(int(self.agflow.checkBox_3.isChecked()))
            dat=funcion_t(int(self.agflow.checkBox_4.isChecked()))
            use_file=funcion_t(int(self.agflow.checkBox_5.isChecked()))
            reas=int(self.agflow.checkBox_6.isChecked())
            path = str(self.agflow.lineEdit_8.text())
        except:
            iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning, duration=10)
            return
        #Se obteiene el texto de un archivo rasfor (un ejemplo) para luego añadirle los valores que se han escogido en el plugin
        fichero = open(self.plugin_dir+r"\Documentos\agflow.inp","r+")
        texto = fichero.read()
        fichero.close()
        #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
        lista_parametros = [slope,maxim_d,maxim_pl,maxim_ps,use,write,arc,dat,use_file]
        lista = [237,244,250,260,265,270,275,280,285]
        texto_nuevo = texto
        contador = 0
        for i in range(len(lista_parametros)):
            texto_nuevo = texto_nuevo[0:lista[i]+contador]+str(lista_parametros[i])+texto_nuevo[lista[i]+contador+1:]
            contador += len(str(lista_parametros[i]))-1
        try:
            f = open(self.direccion+"\\"+"agflow.inp","w+")
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the DEDNM data first select de DEM you are going to use",level=Qgis.Warning, duration=10)
            return 
        f.write(texto_nuevo)
        f.close()
        self.agflow.close()
        df = pd.DataFrame(data = {"REASSIGN":[reas],"ASC_PATH":[path]})
        df.to_csv(self.direccion+"\\"+"agflow.csv", index=False, float_format='%.5f')
        
    def asignar_valores_control_dialogo(self):
        #Añadir los valores del control file al plugin
        #Primero el error para de si no se ha seleccionado el DEM y por lo tanto no existe self.direccion
        if hasattr(self,"direccion"):
            pass
        else:
            iface.messageBar().pushMessage("Select a DEM", "To view the parameters of the control files and to modify them, first select the dem which will be in the same folder as the control files",level=Qgis.Warning, duration=10)
            return 
        #TOPAGNPS
        try:
            control_file = pd.read_csv(self.direccion+"\\"+"TOPAGNPS.csv",encoding = "ISO-8859-1",delimiter=",")
        except:
            return 
        columnas = ["FILENAME","FORMAT","DEMPROC","OUTFORMAT","CSA","MSCL","UTME","UTMN","ROWS","COLS","CELLSIZE","NODATA","OUTSNAP","DNMCNT","DEMEDGE","VERBOSE","KEEPFILES","OPTIMIZE","OUTCOL","OUTROW"]
        dialogos = [self.ctopagnps.lineEdit_7,0,self.ctopagnps.lineEdit_5,self.ctopagnps.lineEdit_14,self.ctopagnps.lineEdit_3,self.ctopagnps.lineEdit_10,self.ctopagnps.lineEdit_19,self.ctopagnps.lineEdit_20,self.ctopagnps.lineEdit_18,self.ctopagnps.lineEdit_2,self.ctopagnps.lineEdit,self.ctopagnps.lineEdit_11,self.ctopagnps.lineEdit_17,self.ctopagnps.lineEdit_6,self.ctopagnps.lineEdit_4,self.ctopagnps.lineEdit_21,self.ctopagnps.lineEdit_9,self.ctopagnps.lineEdit_12,self.ctopagnps.lineEdit_15,self.ctopagnps.lineEdit_22]
        for i in range(len(columnas)):
            try:
                if str(control_file[columnas[i]].iloc[0]) == "nan":
                    texto = ""
                else:
                    texto = str(control_file[columnas[i]].iloc[0])
                dialogos[i].setText(texto)
            except:
                pass
        
        #PEG
        try:
            control_file = pd.read_csv(self.direccion+"\\"+"PEG.csv",encoding = "ISO-8859-1",delimiter=",")
        except:
            pass
        columnas =["Input","CTI_value","Accum_pct"]
        dialogos = [self.cpeg.lineEdit,self.cpeg.lineEdit_2,self.cpeg.lineEdit_3]
        for i in range(len(columnas)):
            try:
                if str(control_file[columnas[i]].iloc[0]) == "nan":
                    texto = ""
                else:
                    texto = str(control_file[columnas[i]].iloc[0])
                dialogos[i].setText(texto)
            except:
                pass

        #AGBUF
        try:
            control_file = pd.read_csv(self.direccion+"\\"+"AgBuf.csv",encoding = "ISO-8859-1",delimiter=",")
        except:
            pass
        columnas =["BUFFER","VEGETATION","FOREST","GRASS","C_THRESHOLD","R_THRESHOLD","UNITS"]
        dialogos = [self.cagbuf.lineEdit,self.cagbuf.lineEdit_2,self.cagbuf.lineEdit_3,self.cagbuf.lineEdit_4,self.cagbuf.lineEdit_5,self.cagbuf.lineEdit_6,self.cagbuf.lineEdit_7]
        for i in range(len(columnas)):
            try:
                if str(control_file[columnas[i]].iloc[0]) == "nan":
                    texto = ""
                else:
                    texto = str(control_file[columnas[i]].iloc[0])
                dialogos[i].setText(texto)
            except:
                pass
        
        #AGWET
        try:
            control_file = pd.read_csv(self.direccion+"\\"+"AgWet.csv",encoding = "ISO-8859-1",delimiter=",")
        except:
            pass
        columnas =["FILENAME","BREACH_BARRIER","BARRIER_HEIGHT_OPTION","BARRIER_HEIGHT","BARRIER_HEIGHT_INCREMENT","BARRIER_HEIGHT_MAX","WETLAND_ID_OPTION","EROSION_INDEX_OPTION","EROSION_INDEX_THRESHOLD","DA_THRESHOLD","WI_THRESHOLD","MIN_WETLAND_RATIO","MAX_WETLAND_RATIO","BUFFER_WIDTH","BUFFER_EXTENT_OPTION","BUFFER_IDS_FILENAME","BUFFER_VEG_FILENAME","BUFFER_ZONE_FILENAME","ASC_PATH","CSV_PATH"]
        dialogos = [self.cagwet.lineEdit,self.cagwet.lineEdit_18,self.cagwet.lineEdit_17,self.cagwet.lineEdit_11,self.cagwet.lineEdit_12,self.cagwet.lineEdit_14,self.cagwet.lineEdit_21,self.cagwet.lineEdit_20,self.cagwet.lineEdit_8,self.cagwet.lineEdit_9,self.cagwet.lineEdit_7,self.cagwet.lineEdit_13,self.cagwet.lineEdit_10,self.cagwet.lineEdit_15,self.cagwet.lineEdit_19,self.cagwet.lineEdit_2,self.cagwet.lineEdit_3,self.cagwet.lineEdit_4,self.cagwet.lineEdit_5,self.cagwet.lineEdit_6]
        for i in range(len(columnas)):
            try:
                if str(control_file[columnas[i]].iloc[0]) == "nan":
                    texto = ""
                else:
                    texto = str(control_file[columnas[i]].iloc[0])
                dialogos[i].setText(texto)
            except:
                pass
        
        #CONCEPTS
        try:
            control_file = pd.read_csv(self.direccion+"\\"+"CONCEPTS.csv",encoding = "ISO-8859-1",delimiter=",")
        except:
            pass
        columnas =["UPSTREAM_REACH_ID","DOWNSTREAM_REACH_ID"]
        dialogos = [self.cconcepts.lineEdit,self.cconcepts.lineEdit_2]
        for i in range(len(columnas)):
            try:
                if str(control_file[columnas[i]].iloc[0]) == "nan":
                    texto = ""
                else:
                    texto = str(control_file[columnas[i]].iloc[0])
                dialogos[i].setText(texto)
            except:
                pass
        
        #POTHOLE
        try:
            control_file = pd.read_csv(self.direccion+"\\"+"POTHOLE.csv",encoding = "ISO-8859-1",delimiter=",")
        except:
            pass
        columnas =["POTHOLE_OPTION","POTHOLE_SURFACE_AREA"]
        dialogos = [self.cpothole.lineEdit,self.cpothole.lineEdit_2]
        for i in range(len(columnas)):
            try:
                if str(control_file[columnas[i]].iloc[0]) == "nan":
                    texto = ""
                else:
                    texto = str(control_file[columnas[i]].iloc[0])
                dialogos[i].setText(texto)
            except:
                pass
    
    def outputs(self):
        #Método para mostrar los resultados de la simulación
        self.output.show()
    
    def output_topagnps(self,output_type):
        #Método para mostrar los outputs de TopAGNPS
        #Se pone el epsg del proyecto
        self.epsg = QgsProject.instance().crs().authid()
        #Primero se pone condición para que se haya elegido el DEM
        if self.output.lineEdit_2.text()=="":
            iface.messageBar().pushMessage("Select a DEM", "To view the outputs first select the DEM that will be in the folder containing the results",level=Qgis.Warning, duration=10)
            return
        #Se pone una función para cambiar coordenadas y otra para la dirección de ficheros que será usada luego por varios
        def change_coordinates(filename,outputname):
            input_raster = gdal.Open(fichero(filename))
            output_raster = fichero(outputname)
            warp = gdal.Warp(output_raster,input_raster,dstSRS=self.epsg)
            warp = None # Closes the files
        def fichero(nombre):
            return self.output.lineEdit_2.text()+"\\"+nombre
     
        #CELDAS RASTER
        if output_type == "Cell_raster":
            if not os.path.exists(fichero("AnnAGNPS_Cell_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Cell_IDs.asc does not exist",level=Qgis.Warning, duration=10)
                return 
            change_coordinates("AnnAGNPS_Cell_IDs.asc","AnnAGNPS_Cell_IDs_EPSG.asc")
            layer = QgsRasterLayer(fichero("AnnAGNPS_Cell_IDs_EPSG.asc"),"Cells_ras")
            QgsProject.instance().addMapLayer(layer)
                
        #CELDAS VECTORIAL
        elif output_type == "Cell_vectorial":
            if not os.path.exists(fichero("AnnAGNPS_Cell_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Cell_IDs.asc does not exist",level=Qgis.Warning, duration=10)
                return
            if not os.path.exists(fichero("cell.gpkg")):
                change_coordinates("AnnAGNPS_Cell_IDs.asc","cell_1.asc")
                processing.run("grass7:r.to.vect", {'input':fichero("cell_1.asc"),
                    'type':2,'column':'value','-s':False,
                    '-v':False,'-z':False,'-b':False,'-t':False,
                    'output':fichero("cell.gpkg"),'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':False})
            #Esta función es para crear una copia de archivo y que las columnas se añadan ahí
            def copiar_archivo(input_file,output):
                processing.run("native:savefeatures", 
                    {'INPUT':fichero(input_file),
                    'OUTPUT':fichero(output),
                    'LAYER_NAME':'','DATASOURCE_OPTIONS':'','LAYER_OPTIONS':''})
            try:
                copiar_archivo("cell.gpkg","cell_out.gpkg")
            except:
                iface.messageBar().pushMessage("Delete layers", "To add cell layer remove Cells_vec.",level=Qgis.Warning, duration=10)
                return
            layer = QgsVectorLayer(fichero("cell_out.gpkg"),"Cells_vec")
            #Borrar columnas que no son las que queremos
            columnas_borrar = [x.name() for x in layer.fields() if x.name()!="fid" and x.name()!="value" and x.name()!="Cell_ID"]
            field_index = [layer.fields().indexFromName(x) for x in columnas_borrar]
            data_provider = layer.dataProvider()
            layer.startEditing()
            data_provider.deleteAttributes(field_index)
            layer.updateFields()
            layer.commitChanges()
            #Cambiar el nombre de la columna value por Cell_ID
            for field in layer.fields():
                if field.name() == 'value':
                    with edit(layer):
                        idx = layer.fields().indexFromName(field.name())
                        layer.renameAttribute(idx, 'Cell_ID')
            QgsProject.instance().addMapLayer(layer)
            #Poner etiquetas
            label_settings = QgsPalLayerSettings()
            label_settings.enabled = True
            label_settings.fieldName = "Cell_ID"
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 12))
            text_format.setSize(15)
            label_settings.setFormat(text_format)
            layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
            layer.setLabelsEnabled(True)
            layer.triggerRepaint()
        
        #DELIMITACIÓN DE LA CUENCA RASTER
        elif output_type == "Boundary_raster":
            if not os.path.exists(fichero("BOUND.ASC")):
                iface.messageBar().pushMessage("Output not found", "BOUND.ASC does not exist",level=Qgis.Warning, duration=10)
                return
            change_coordinates("BOUND.ASC","BOUND_EPSG.ASC")
            layer = QgsRasterLayer(fichero("BOUND_EPSG.ASC"),"Watershed_boundary_ras")
            QgsProject.instance().addMapLayer(layer)
            
        #DELIMITACIÓN DE LA CUENCA VECTORIAL
        elif output_type == "Boundary_vectorial":
            if not os.path.exists(fichero("BOUND.ASC")):
                iface.messageBar().pushMessage("Output not found", "BOUND.ASC does not exist",level=Qgis.Warning, duration=10)
                return
            if not os.path.exists(fichero("bound.gpkg")):
                change_coordinates("BOUND.ASC","BOUND_EPSG.ASC")
                processing.run("grass7:r.to.vect", {'input':fichero("BOUND_EPSG.ASC"),
                    'type':2,'column':'value','-s':False,
                    '-v':False,'-z':False,'-b':False,'-t':False,
                    'output':fichero("bound.gpkg"),'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(fichero("bound.gpkg"),"Watershed_boundary_vec")
            QgsProject.instance().addMapLayer(layer)
            
        #REACHES RASTER
        elif output_type == "Reaches_raster":
            if not os.path.exists(fichero("AnnAGNPS_Reach_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Reach_IDs.asc does not exist",level=Qgis.Warning, duration=10)
                return
            change_coordinates("AnnAGNPS_Reach_IDs.asc","AnnAGNPS_Reach_IDs_EPSG.asc")
            layer = QgsRasterLayer(fichero("AnnAGNPS_Reach_IDs_EPSG.asc"),"Reaches_ras")
            QgsProject.instance().addMapLayer(layer)
        
        #REACHES VECTORIAL
        elif output_type == "Reaches_vectorial":
            if not os.path.exists(fichero("AnnAGNPS_Reach_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Reach_IDs.asc does not exist",level=Qgis.Warning, duration=10)
                return
            if not os.path.exists(fichero("reaches.gpkg")):
                change_coordinates("AnnAGNPS_Reach_IDs.asc","AnnAGNPS_Reach_IDs_EPSG.asc")
                processing.run("grass7:r.to.vect", {'input':fichero("AnnAGNPS_Reach_IDs_EPSG.asc"),
                    'type':0,'column':'value','-s':False,
                    '-v':False,'-z':False,'-b':False,'-t':False,
                    'output':fichero("reaches.gpkg"),'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(fichero("reaches.gpkg"),"Reaches_vec")
            #Borrar columnas que no son las que queremos
            columnas_borrar = [x.name() for x in layer.fields() if x.name()!="fid" and x.name()!="value" and x.name()!="Reach_ID"]
            field_index = [layer.fields().indexFromName(x) for x in columnas_borrar]
            data_provider = layer.dataProvider()
            layer.startEditing()
            data_provider.deleteAttributes(field_index)
            layer.updateFields()
            layer.commitChanges()
            #Cambiar el nombre de la columna value por Reach_ID
            for field in layer.fields():
                if field.name() == 'value':
                    with edit(layer):
                        idx = layer.fields().indexFromName(field.name())
                        layer.renameAttribute(idx, 'Reach_ID')
            QgsProject.instance().addMapLayer(layer)
            #Poner simbología categorizada
            unique_values = list(set([x["Reach_ID"] for x in layer.getFeatures()]))
            category_colors = {}
            color_ramp = QgsStyle().defaultStyle().colorRamp('Spectral')
            color_count = len(unique_values)
            categories = []
            line_width = 1 
            for i, value in enumerate(unique_values):
                color = color_ramp.color(i / color_count)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.setColor(color)
                symbol.setWidth(line_width)  # Establecer el grosor de línea personalizado
                category = QgsRendererCategory(value, symbol, str(value))
                categories.append(category)
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(QColor(200, 200, 200))  # Color gris para "Otros"
            symbol.setWidth(line_width)  # Establecer el grosor de línea personalizado
            category = QgsRendererCategory("Otros", symbol, "Otros")
            categories.append(category)
            renderer = QgsCategorizedSymbolRenderer("Reach_ID", categories)
            layer.setRenderer(renderer)
            layer.triggerRepaint()
        
        #ACCUMULATED AREA
        elif output_type == "Accumulated":
            if not os.path.exists(fichero("UPAREA.asc")):
                iface.messageBar().pushMessage("Output not found", "UPAREA.asc does not exist",level=Qgis.Warning, duration=10)
                return
            layer = QgsRasterLayer(fichero("UPAREA.asc"),"Accumulated_area")
            QgsProject.instance().addMapLayer(layer)
        
        #TERRAIN SLOPE
        elif output_type == "Terrain_slope":
            if not os.path.exists(fichero("TSLOPE.ASC")):
                iface.messageBar().pushMessage("Output not found", "TSLOPE.ASC does not exist",level=Qgis.Warning, duration=10)
                return
            layer = QgsRasterLayer(fichero("TSLOPE.ASC"),"Terrain_slope")
            QgsProject.instance().addMapLayer(layer)
        
        #HYDRAULIC SLOPE
        elif output_type == "Hydraulic":
            if not os.path.exists(fichero("HSLOPE.ASC")):
                iface.messageBar().pushMessage("Output not found", "HSLOPE.ASC does not exist",level=Qgis.Warning, duration=10)
                return
            layer = QgsRasterLayer(fichero("HSLOPE.ASC"),"Hydraulic_slope")
            QgsProject.instance().addMapLayer(layer)

        #TERRAIN ASPECT
        elif output_type == "Terrain_aspect":
            if not os.path.exists(fichero("TASPEC.ASC")):
                iface.messageBar().pushMessage("Output not found", "TASPEC.ASC does not exist",level=Qgis.Warning, duration=10)
                return
            layer = QgsRasterLayer(fichero("TASPEC.ASC"),"Terrain_aspect")
            QgsProject.instance().addMapLayer(layer)
        
        #RUSLE LS FACTOR
        elif output_type == "RUSLE":
            if not os.path.exists(fichero("AgFlow_LS_Factor.asc")):
                iface.messageBar().pushMessage("Output not found", "AgFlow_LS_Factor.asc does not exist",level=Qgis.Warning, duration=10)
                return
            layer = QgsRasterLayer(fichero("AgFlow_LS_Factor.asc"),"RUSLE_LS_factor")
            QgsProject.instance().addMapLayer(layer)
        
        #CELL LONGEST FLOW PATH RASTER
        elif output_type == "Longest_raster":
            if not os.path.exists(fichero("AgFlow_Cell_Longest_Flow_Path.asc")):
                iface.messageBar().pushMessage("Output not found", "AgFlow_Cell_Longest_Flow_Path.asc does not exist",level=Qgis.Warning, duration=10)
                return
            layer = QgsRasterLayer(fichero("AgFlow_Cell_Longest_Flow_Path.asc"),"Cell_longest_flow_raster")
            QgsProject.instance().addMapLayer(layer)

        #CELL LONGEST FLOW PATH VECTORIAL
        elif output_type == "Longest_vectorial":
            if not os.path.exists(fichero("AgFlow_Cell_Longest_Flow_Path.asc")):
                iface.messageBar().pushMessage("Output not found", "AgFlow_Cell_Longest_Flow_Path.asc does not exist",level=Qgis.Warning, duration=10)
                return
            if not os.path.exists(fichero("longpath.gpkg")):
                change_coordinates("AgFlow_Cell_Longest_Flow_Path.asc","AgFlow_Cell_Longest_Flow_Path_epsg.asc")
                processing.run("grass7:r.to.vect", {'input':fichero("AgFlow_Cell_Longest_Flow_Path_epsg.asc"),
                    'type':0,'column':'value','-s':False,
                    '-v':False,'-z':False,'-b':False,'-t':False,
                    'output':fichero("longpath.gpkg"),'GRASS_REGION_PARAMETER':None,
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(fichero("longpath.gpkg"),"Cell_longest_flow_raster_vec")
            QgsProject.instance().addMapLayer(layer)
            #Cambio de formato de la capa
            symbol = QgsLineSymbol()
            symbol.setWidth(1)
            symbol.setColor(QColor.fromRgb(255, 0, 0))
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            layer.triggerRepaint()

    def files_directory(self):
        #Método para añadir la dirección de la carpeta del mdt a la interfaz de los inputs de AnnAGNPS
        lista = [self.inputs.l_1,self.inputs.l_23,self.inputs.l_47,self.inputs.l_53]
        for i in lista:
            if i.text()=="":
                i.setText(str(self.mdt_directory))
        
    def add_master(self):
        #Método para añadir la información de un archivo master a los inputs de AnnAGNPS
        #Se abre la opción de escoger archivo y se obtiene la información
        if hasattr(self, 'mdt_directory'):
            fname = QFileDialog.getOpenFileName(self.inputs,"Select master file",self.mdt_directory,"CSV files (*.csv)")
        else:
            fname = QFileDialog.getOpenFileName(self.inputs,"Select master file","C/","CSV files (*.csv)")
        if fname[0]!="":
            try:
                master_df = pd.read_csv(fname[0],encoding = "ISO-8859-1",delimiter=",")
            except:
                return
            #Se ponen todas las lineas de texto vacias
            for i in [self.inputs.l_1,self.inputs.l_2,self.inputs.l_3,self.inputs.l_4,self.inputs.l_5,self.inputs.l_6,self.inputs.l_7,self.inputs.l_8,self.inputs.l_9,self.inputs.l_10,self.inputs.l_11,self.inputs.l_12,self.inputs.l_13,self.inputs.l_14,self.inputs.l_15,self.inputs.l_16,self.inputs.l_17,self.inputs.l_18,self.inputs.l_19,self.inputs.l_20,self.inputs.l_21,self.inputs.l_22,self.inputs.l_23,self.inputs.l_24,self.inputs.l_25,self.inputs.l_26,self.inputs.l_27,self.inputs.l_28,self.inputs.l_29,self.inputs.l_30,self.inputs.l_31,self.inputs.l_32,self.inputs.l_33,self.inputs.l_34,self.inputs.l_35,self.inputs.l_36,self.inputs.l_37,self.inputs.l_38,self.inputs.l_39,self.inputs.l_40,self.inputs.l_41,self.inputs.l_42,self.inputs.l_43,self.inputs.l_44,self.inputs.l_45,self.inputs.l_46,self.inputs.l_47,self.inputs.l_48,self.inputs.l_49,self.inputs.l_50,self.inputs.l_51,self.inputs.l_52,self.inputs.l_53,self.inputs.l_54,self.inputs.l_55,self.inputs.l_56,self.inputs.l_57,self.inputs.l_58,self.inputs.l_59,self.inputs.l_60,self.inputs.l_61,self.inputs.l_62,self.inputs.l_63,self.inputs.l_64,self.inputs.l_65,self.inputs.l_66,self.inputs.l_67,self.inputs.l_68,self.inputs.l_69,self.inputs.l_70,self.inputs.l_71]:
                i.setText("")
            #Creación de diccionario que contiene las lineas de texto en donde hay que poner el nombre del archivo que contiene a cada sección 
            master_dict = {"AnnAGNPS ID":self.inputs.l_54,"Aquaculture Pond Data":self.inputs.l_2,
                               "Aquaculture Schedule Data":self.inputs.l_24,"Cell Data":self.inputs.l_3,"Classic Gully Data":self.inputs.l_4,
                               "Contour Data":self.inputs.l_25,"Crop Data":self.inputs.l_26,"Crop Growth Data":self.inputs.l_27,
                               "Ephemeral Gully Data":self.inputs.l_5,"Feedlot Data":self.inputs.l_6,"Feedlot Management Data":self.inputs.l_28,
                               "Fertilizer Application Data":self.inputs.l_29,"Fertilizer Reference Data":self.inputs.l_30,
                               "Field Pond Data":self.inputs.l_7,"Geology Data":self.inputs.l_31,
                               "Global Error and Warning Limits Data":self.inputs.l_55,"Global IDs Factors and Flags Data":self.inputs.l_56,
                               "Hydraulic Geometry Data":self.inputs.l_32,"Impoundment Data":self.inputs.l_8,
                               "Irrigation Application Data":self.inputs.l_33,"Management Field Data":self.inputs.l_34,
                               "Management Operation Data":self.inputs.l_35,"Management Schedule Data":self.inputs.l_36,
                               "Non-Crop Data":self.inputs.l_37,
                               "Pesticide Application Data":self.inputs.l_38,"Pesticide Initial Conditions Data":self.inputs.l_57,
                               "Pesticide Reference Data":self.inputs.l_39,"PL Calibration Data":self.inputs.l_58,
                               "Point Source Data":self.inputs.l_9,"RCN Calibration Data":self.inputs.l_59,"Reach Data":self.inputs.l_10,
                               "Reach Nutrient Half-life Data":self.inputs.l_40,"Runoff Curve Number Data":self.inputs.l_42,
                               "Simulation Period Data":self.inputs.l_60,"Soil Data":self.inputs.l_43,"Soil Layer Data":self.inputs.l_44,
                               "Soil Initial Conditions Data":self.inputs.l_61,"Strip Crop Data":self.inputs.l_45,
                               "Tile Drain Data":self.inputs.l_46,"Watershed Data":self.inputs.l_12,"EI Pct Data":self.inputs.l_50,
                               "STORM TYPE DATA - RFD":self.inputs.l_51,"STORM TYPE DATA - UPDRC":self.inputs.l_52,
                               "Output Options - Global":self.inputs.l_63,"Output Options - AA":self.inputs.l_68,"Output Options - EV":self.inputs.l_69,
                               "Output Options - CSV":self.inputs.l_64,"Output Options - DPP":self.inputs.l_65,
                               "Output Options - NPT":self.inputs.l_66,"Output Options - SIM":self.inputs.l_67,
                               "Output Options - TBL":self.inputs.l_70,"Output Options - MN/MX":self.inputs.l_71,
                               "Output Options - Cell":self.inputs.l_14,"Output Options - Feedlot":self.inputs.l_15,
                               "Output Options - Field Pond":self.inputs.l_16,
                               "Output Options - Classic Gully":self.inputs.l_17,
                               "Output Options - Ephemeral Gully":self.inputs.l_18,
                               "Output Options - Impoundment":self.inputs.l_19,
                               "Output Options - Point Source":self.inputs.l_20,
                               "Output Options - Reach":self.inputs.l_21,
                               "Output Options - Wetland":self.inputs.l_22,
                               "CLIMATE DATA - STATION":self.inputs.l_48,
                               "CLIMATE DATA - DAILY":self.inputs.l_49,"Wetland Data":self.inputs.l_13,"Riparian Buffer Data":self.inputs.l_41,
                               "RUSLE2 Data":self.inputs.l_62,"RiceWQ Data":self.inputs.l_11}
            inverted_dic = {value: key for key, value in master_dict.items()}
            #Aquí se añade a cada linea de texto (lineEdit) la dirección que habría que poner, teniendo en cuenta que se puede poner en formato .\general etc. o la dirección completa
            dic_watershed = {}
            dic_general = {}
            dic_climate = {}
            dic_simulation = {}
            for k,i in enumerate(self.lines_dialog):
                try:
                    if k<21:
                        if master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0][0]==".":
                            dic_watershed[i]=os.path.split(fname[0])[0]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[1]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[-1]
                        else:
                            dic_watershed[i]=master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]
                    elif 21<=k<44:
                        if master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0][0]==".":
                            dic_general[i]=os.path.split(fname[0])[0]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[1]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[-1]
                        else:
                            dic_general[i]=master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]
                    elif 44<=k<49:
                        if master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0][0]==".":
                            dic_climate[i]=os.path.split(fname[0])[0]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[1]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[-1]
                        else:
                            dic_climate[i]=master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]
                    elif 49<=k<67:
                        if master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0][0]==".":
                            dic_simulation[i]=os.path.split(fname[0])[0]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[1]+"/"+r"{}".format(master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]).split("\\")[-1]
                        else:
                            dic_simulation[i]=master_df[master_df["Data Section ID"]==inverted_dic[i]]["File Name"].iloc[0]
                except:
                    pass
            #Se pone el nombre de la carpeta que más se repite para cada sección
            self.inputs.l_1.setText(statistics.mode([os.path.split(x)[0] for x in dic_watershed.values()]))
            self.inputs.l_23.setText(statistics.mode([os.path.split(x)[0] for x in dic_general.values()]))
            self.inputs.l_47.setText(statistics.mode([os.path.split(x)[0] for x in dic_climate.values()]))
            self.inputs.l_53.setText(statistics.mode([os.path.split(x)[0] for x in dic_simulation.values()]))
            
            #Se añaden los nombres de los archivos. Si la carpeta que se ha puesto es la misma del archivo entonces se pone solo el nombre del archivo, sino toda la dirección. 
            #Watershed
            for i in dic_watershed.keys():
                if os.path.dirname(dic_watershed[i])==self.inputs.l_1.text():
                    i.setText(os.path.split(dic_watershed[i])[1])
                else:
                    i.setText(dic_watershed[i])
            #General
            for i in dic_general.keys():
                if os.path.dirname(dic_general[i])==self.inputs.l_23.text():
                    i.setText(os.path.split(dic_general[i])[1])
                else:
                    i.setText(dic_general[i])
            #Climate
            for i in dic_climate.keys():
                if os.path.dirname(dic_climate[i])==self.inputs.l_47.text():
                    i.setText(os.path.split(dic_climate[i])[1])
                else:
                    i.setText(dic_climate[i])
            #Simulation
            for i in dic_simulation.keys():
                if os.path.dirname(dic_simulation[i])==self.inputs.l_53.text():
                    i.setText(os.path.split(dic_simulation[i])[1])
                else:
                    i.setText(dic_simulation[i])
    def delete_lines(self, section):
        #Método para borrar las líneas de diálog en el annagnps input dialog
        #Borrar líneas de texto
        if section=="watershed":
            for i in [self.inputs.l_1,self.inputs.l_2, self.inputs.l_3, self.inputs.l_4, self.inputs.l_5, self.inputs.l_6, self.inputs.l_7, self.inputs.l_8, self.inputs.l_9, self.inputs.l_10, self.inputs.l_11, self.inputs.l_12, self.inputs.l_13, self.inputs.l_14, self.inputs.l_15, self.inputs.l_16, self.inputs.l_17, self.inputs.l_18, self.inputs.l_19, self.inputs.l_20, self.inputs.l_21, self.inputs.l_22]:
                i.setText("")
        if section=="general":
            for i in [self.inputs.l_23,self.inputs.l_24, self.inputs.l_25, self.inputs.l_26, self.inputs.l_27, self.inputs.l_28, self.inputs.l_29, self.inputs.l_30, self.inputs.l_31, self.inputs.l_32, self.inputs.l_33, self.inputs.l_34, self.inputs.l_35, self.inputs.l_36, self.inputs.l_37, self.inputs.l_38, self.inputs.l_39, self.inputs.l_40, self.inputs.l_41, self.inputs.l_42, self.inputs.l_43, self.inputs.l_44, self.inputs.l_45, self.inputs.l_46]:
                i.setText("")
        if section=="climate":
            for i in [self.inputs.l_47,self.inputs.l_48, self.inputs.l_49, self.inputs.l_50, self.inputs.l_51, self.inputs.l_52]:
                i.setText("")
        if section=="simulation":
            for i in [self.inputs.l_53,self.inputs.l_54, self.inputs.l_55, self.inputs.l_56, self.inputs.l_57, self.inputs.l_58, self.inputs.l_59, self.inputs.l_60, self.inputs.l_61, self.inputs.l_62, self.inputs.l_63, self.inputs.l_64, self.inputs.l_65, self.inputs.l_66, self.inputs.l_67, self.inputs.l_68, self.inputs.l_69, self.inputs.l_70, self.inputs.l_71]:
                i.setText("")
        #Borrar el topagnps provided
        if section=="watershed":
            for i in [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3]:
                i.setChecked(False)
        if section=="general":
            self.inputs.checkBox_4.setChecked(False)
        
    def change_directory_input(self,section):
        #Método para cambiar el directorio de las secciones en el diálog de AnnAGNPS input editor
        if section =="watershed":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.mdt_directory)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_1.setText(fname)
        if section =="general":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.mdt_directory)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_23.setText(fname)
        if section =="climate":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.mdt_directory)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_47.setText(fname)
        if section =="simulation":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.mdt_directory)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_53.setText(fname)
                
    def save_project(self):
        #Método para guardar el proyecto
        
        # Se abre el cuadro de diálogo para guardar el archivo
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("CSV files (*.csv)")
        file_dialog.setDefaultSuffix("csv")
        
        #Se obtienen los datos de los inputs
        layers = QgsProject.instance().layerTreeRoot().children()
        if self.dlg.comboBox.currentIndex()>0:
            dem_layer = layers[self.dlg.comboBox.currentIndex() - 1].layer().dataProvider().dataSourceUri()
            dem_name = layers[self.dlg.comboBox.currentIndex() - 1].layer().name()
        else:
            dem_layer = ""
            dem_name =""
        if self.dlg.cbSoil.currentIndex()>0:
            soil_layer = layers[self.dlg.cbSoil.currentIndex()-1].layer().dataProvider().dataSourceUri()
            soil_name = layers[self.dlg.cbSoil.currentIndex()-1].layer().name()
            soil_column = [field.name() for field in layers[self.dlg.cbSoil.currentIndex()-1].layer().fields()][self.dlg.cbColumnSoil.currentIndex()]
        else:
            soil_layer = ""
            soil_name = ""
            soil_column = ""
        if self.dlg.cbMan.currentIndex()>0:
            use_layer = layers[self.dlg.cbMan.currentIndex()-1].layer().dataProvider().dataSourceUri()
            use_name = layers[self.dlg.cbMan.currentIndex()-1].layer().name()
            try:
                use_column = [field.name() for field in layers[self.dlg.cbMan.currentIndex()-1].layer().fields()][self.dlg.cbColumnMan.currentIndex()]
            except:
                use_column=""
        else:
            use_layer = ""
            use_name = ""
            use_column = ""
        if self.dlg.comboBox_2.currentIndex()>0:
            buffer_layer = layers[self.dlg.comboBox_2.currentIndex()-1].layer().dataProvider().dataSourceUri()
            buffer_name = layers[self.dlg.comboBox_2.currentIndex()-1].layer().name()
        else:
            buffer_layer = ""
            buffer_name = ""
        if self.dlg.comboBox_3.currentIndex()>0:
            vegetation_layer = layers[self.dlg.comboBox_3.currentIndex()-1].layer().dataProvider().dataSourceUri()
            vegetation_name = layers[self.dlg.comboBox_3.currentIndex()-1].layer().name()
        else:
            vegetation_layer = ""
            vegetation_name = ""
        unique_soil = self.dlg.lineEdit.text()
        unique_landuse = self.dlg.lineEdit_2.text()
        # Se crea el diccionario en el que se asigna a cada entrada un valor
        dic_save = {"Input":"value","dem": dem_layer,"dem_name":dem_name,"soil_layer":soil_layer,"soil_name":soil_name,"soil_column":soil_column,"use_layer":use_layer,"use_name":use_name,"use_column":use_column,
            "buffer_layer":buffer_layer,"buffer_name":buffer_name,"vegetation_layer":vegetation_layer,"vegetation_name":vegetation_name,"unique_soil":unique_soil,"unique_landuse":unique_landuse,
            "add_outlet":self.dlg.checkBox_2.isChecked(),"execute_topagnps":self.dlg.cbTop.isChecked(),"execute_annagnps":self.dlg.cbAnn.isChecked(),
            "watershed_directory":self.inputs.l_1.text(),
            "general_directory":self.inputs.l_23.text(),"climate_directory":self.inputs.l_47.text(),
            "simulation_directory":self.inputs.l_53.text(),"cell_topagpns_provided":self.inputs.checkBox.isChecked(),"eg_topagpns_provided":self.inputs.checkBox_2.isChecked(),
            "reach_topagpns_provided":self.inputs.checkBox_3.isChecked(),"riparian_topagpns_provided":self.inputs.checkBox_4.isChecked()}
        #A este diccionario se le añaden los inputs de AnnAGNPS
        master_dict = {"AnnAGNPS ID":self.inputs.l_54,"Aquaculture Pond Data":self.inputs.l_2,
                               "Aquaculture Schedule Data":self.inputs.l_24,"Cell Data":self.inputs.l_3,"Classic Gully Data":self.inputs.l_4,
                               "Contour Data":self.inputs.l_25,"Crop Data":self.inputs.l_26,"Crop Growth Data":self.inputs.l_27,
                               "Ephemeral Gully Data":self.inputs.l_5,"Feedlot Data":self.inputs.l_6,"Feedlot Management Data":self.inputs.l_28,
                               "Fertilizer Application Data":self.inputs.l_29,"Fertilizer Reference Data":self.inputs.l_30,
                               "Field Pond Data":self.inputs.l_7,"Geology Data":self.inputs.l_31,
                               "Global Error and Warning Limits Data":self.inputs.l_55,"Global IDs Factors and Flags Data":self.inputs.l_56,
                               "Hydraulic Geometry Data":self.inputs.l_32,"Impoundment Data":self.inputs.l_8,
                               "Irrigation Application Data":self.inputs.l_33,"Management Field Data":self.inputs.l_34,
                               "Management Operation Data":self.inputs.l_35,"Management Schedule Data":self.inputs.l_36,
                               "Non-Crop Data":self.inputs.l_37,
                               "Pesticide Application Data":self.inputs.l_38,"Pesticide Initial Conditions Data":self.inputs.l_57,
                               "Pesticide Reference Data":self.inputs.l_39,"PL Calibration Data":self.inputs.l_58,
                               "Point Source Data":self.inputs.l_9,"RCN Calibration Data":self.inputs.l_59,"Reach Data":self.inputs.l_10,
                               "Reach Nutrient Half-life Data":self.inputs.l_40,"Runoff Curve Number Data":self.inputs.l_42,
                               "Simulation Period Data":self.inputs.l_60,"Soil Data":self.inputs.l_43,"Soil Layer Data":self.inputs.l_44,
                               "Soil Initial Conditions Data":self.inputs.l_61,"Strip Crop Data":self.inputs.l_45,
                               "Tile Drain Data":self.inputs.l_46,"Watershed Data":self.inputs.l_12,"EI Pct Data":self.inputs.l_50,
                               "STORM TYPE DATA - RFD":self.inputs.l_51,"STORM TYPE DATA - UPDRC":self.inputs.l_52,
                               "Output Options - Global":self.inputs.l_63,"Output Options - AA":self.inputs.l_68,"Output Options - EV":self.inputs.l_69,
                               "Output Options - CSV":self.inputs.l_64,"Output Options - DPP":self.inputs.l_65,
                               "Output Options - NPT":self.inputs.l_66,"Output Options - SIM":self.inputs.l_67,
                               "Output Options - TBL":self.inputs.l_70,"Output Options - MN/MX":self.inputs.l_71,
                               "Output Options - Cell":self.inputs.l_14,"Output Options - Feedlot":self.inputs.l_15,
                               "Output Options - Field Pond":self.inputs.l_16,
                               "Output Options - Classic Gully":self.inputs.l_17,
                               "Output Options - Ephemeral Gully":self.inputs.l_18,
                               "Output Options - Impoundment":self.inputs.l_19,
                               "Output Options - Point Source":self.inputs.l_20,
                               "Output Options - Reach":self.inputs.l_21,
                               "Output Options - Wetland":self.inputs.l_22,
                               "CLIMATE DATA - STATION":self.inputs.l_48,
                               "CLIMATE DATA - DAILY":self.inputs.l_49,"Wetland Data":self.inputs.l_13,"Riparian Buffer Data":self.inputs.l_41,
                               "RUSLE2 Data":self.inputs.l_62,"RiceWQ Data":self.inputs.l_11}
        #Bucle para añadir los inptus de AnnAGNPS al diccionario que va a guardar
        for i in master_dict.keys():
            dic_save[i] = master_dict[i].text()
        #Se guarda el archivo
        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            # Se guarda el archivo CSV utilizando la API de QGIS
            try:
                with open(file_path, 'w') as file:
                    for key, value in dic_save.items():
                        file.write(f"{key},{value}\n")
            except:
                iface.messageBar().pushMessage("Error Saving Project", f"Please close {file_path}" ,level=Qgis.Warning, duration=10)
    def load_project(self):
        #Método para cargar el proyecto
        #Se abre el archivo
        fname = QFileDialog.getOpenFileName(self.dlg,"Load project","C/","CSV files (*.csv)")
        if fname[0]!="":
            try:
                project_df = pd.read_csv(fname[0],encoding = "ISO-8859-1",delimiter=",")
                #Primero se comprueba que existen las capas que estaban en el proyecto guardado. Si no lo están, se añaden. 
                layers = {"dem":project_df[project_df.iloc[:,0]=="dem"].iloc[0,1],"soil":project_df[project_df.iloc[:,0]=="soil_layer"].iloc[0,1],
                    "use":project_df[project_df.iloc[:,0]=="use_layer"].iloc[0,1],"buffer":project_df[project_df.iloc[:,0]=="buffer_layer"].iloc[0,1],
                    "vegetation":project_df[project_df.iloc[:,0]=="vegetation_layer"].iloc[0,1]}
            except:
                iface.messageBar().pushMessage("Error Loading Project", "The file you have selected does not have the format or information necessary to upload a project. " ,level=Qgis.Warning, duration=10)
                return 
            #Bucle para añadir capas
            names = {"dem":"dem_name","buffer":"buffer_name","vegetation":"vegetation_name"}
            for i in layers.keys():
                layer_exists = False
                for layer in QgsProject.instance().mapLayers().values():
                    if not type (layers[i])==float and os.path.abspath(layer.source()) == os.path.abspath(layers[i]):
                        layer_exists = True
                        break
                if not layer_exists:
                    if (i == "dem" or i == "buffer" or i == "vegetation" ) and not type (layers[i])==float:
                        layer = QgsRasterLayer(layers[i],project_df[project_df.iloc[:,0]==names[i]].iloc[0,1])
                        QgsProject.instance().addMapLayer(layer)
                    elif not type (layers[i])==float:
                        layer = QgsVectorLayer(layers[i],i)
                        QgsProject.instance().addMapLayer(layer)
            
            #Se añaden al combobox la lista de las capas que hay en qgis. Sino, por ejemplo, cuando no tengo capas y cargo, no hay ninguna capa que elegir en el combobox. 
            #Hacer que el desplegable de las columnas se quede vacío después de las cargas anteriores
            self.dlg.comboBox.clear()
            self.dlg.cbSoil.clear()
            self.dlg.cbMan.clear()
            self.dlg.cbColumnSoil.clear()
            self.dlg.cbColumnMan.clear()
            self.dlg.comboBox_2.clear()
            self.dlg.comboBox_3.clear()
            #Añadir al desplegable las capas que están en el proyecto
            combo_lista = [layer.name() for layer in QgsProject.instance().layerTreeRoot().children()]
            combo_lista.insert(0,"")
            try:
                self.dlg.comboBox.addItems(combo_lista)
            except:
                pass
            try:
                self.dlg.cbSoil.addItems(combo_lista)
            except:
                pass
            self.dlg.cbMan.addItems(combo_lista)
            self.dlg.comboBox_2.addItems(combo_lista)
            self.dlg.comboBox_3.addItems(combo_lista)
        
            #Se añaden las capas a los combobox
            layers_l = QgsProject.instance().layerTreeRoot().children()
            sources = [x.layer().source() for x in layers_l]
            comboboxes = [self.dlg.comboBox,self.dlg.cbSoil,self.dlg.cbMan,self.dlg.comboBox_2,self.dlg.comboBox_3]
            names = ["dem", "soil","use","buffer","vegetation"]
            for i in range(len(comboboxes)):
                try:
                    comboboxes[i].setCurrentIndex(sources.index(layers[names[i]])+1)
                except:
                    pass
                    
            #Se añaden las columnas al combobox
            #Función para devolver información del archivo guardado
            def retrieve_data(column_name):
                if str(project_df[project_df.iloc[:,0]==column_name].iloc[0,1])=="nan":
                    return ""
                if str(project_df[project_df.iloc[:,0]==column_name].iloc[0,1])=="False":
                    return False
                if str(project_df[project_df.iloc[:,0]==column_name].iloc[0,1])=="True":
                    return True
                else:
                    return project_df[project_df.iloc[:,0]==column_name].iloc[0,1]
                
            #Soil
            try:
                columns = [field.name() for field in QgsVectorLayer(layers["soil"],"a").fields()]
                self.dlg.cbColumnSoil.setCurrentIndex(columns.index(retrieve_data("soil_column")))
            except:
                pass
            #Use
            try:
                columns = [field.name() for field in QgsVectorLayer(layers["use"],"a").fields()]
                self.dlg.cbColumnMan.setCurrentIndex(columns.index(retrieve_data("use_column")))
            except:
                pass
            try:
                #Se añade información de unique soil y unique use
                self.dlg.lineEdit.setText(str(retrieve_data("unique_soil")))
                self.dlg.lineEdit_2.setText(str(retrieve_data("unique_landuse")))
                #AddOutlet
                self.dlg.checkBox_2.setChecked(retrieve_data("add_outlet"))
                #Execute TopAGNPS
                self.dlg.cbTop.setChecked(retrieve_data("execute_topagnps"))
                #Execute AnnAGNPS
                self.dlg.cbAnn.setChecked(retrieve_data("execute_annagnps"))
                #Información de Provided by TopAGNPS
                self.inputs.checkBox.setChecked(retrieve_data("cell_topagpns_provided"))
                self.inputs.checkBox_2.setChecked(retrieve_data("eg_topagpns_provided"))
                self.inputs.checkBox_3.setChecked(retrieve_data("reach_topagpns_provided"))
                self.inputs.checkBox_4.setChecked(retrieve_data("riparian_topagpns_provided"))
            except:
                iface.messageBar().pushMessage("Error Loading Project", "The file you have selected does not have the format or information necessary to upload a project. " ,level=Qgis.Warning, duration=10)
                return 
            #Inputs de AnnAGNPS
            load_dict = {"watershed_directory":self.inputs.l_1,"general_directory":self.inputs.l_23,"climate_directory":self.inputs.l_47,
                        "simulation_directory":self.inputs.l_53,"AnnAGNPS ID":self.inputs.l_54,
                        "Aquaculture Pond Data":self.inputs.l_2,"Aquaculture Schedule Data":self.inputs.l_24,"Cell Data":self.inputs.l_3,
                       "Classic Gully Data":self.inputs.l_4,
                       "Contour Data":self.inputs.l_25,"Crop Data":self.inputs.l_26,"Crop Growth Data":self.inputs.l_27,
                       "Ephemeral Gully Data":self.inputs.l_5,"Feedlot Data":self.inputs.l_6,"Feedlot Management Data":self.inputs.l_28,
                       "Fertilizer Application Data":self.inputs.l_29,"Fertilizer Reference Data":self.inputs.l_30,
                       "Field Pond Data":self.inputs.l_7,"Geology Data":self.inputs.l_31,
                       "Global Error and Warning Limits Data":self.inputs.l_55,"Global IDs Factors and Flags Data":self.inputs.l_56,
                       "Hydraulic Geometry Data":self.inputs.l_32,"Impoundment Data":self.inputs.l_8,
                       "Irrigation Application Data":self.inputs.l_33,"Management Field Data":self.inputs.l_34,
                       "Management Operation Data":self.inputs.l_35,"Management Schedule Data":self.inputs.l_36,
                       "Non-Crop Data":self.inputs.l_37,
                       "Pesticide Application Data":self.inputs.l_38,"Pesticide Initial Conditions Data":self.inputs.l_57,
                       "Pesticide Reference Data":self.inputs.l_39,"PL Calibration Data":self.inputs.l_58,
                       "Point Source Data":self.inputs.l_9,"RCN Calibration Data":self.inputs.l_59,"Reach Data":self.inputs.l_10,
                       "Reach Nutrient Half-life Data":self.inputs.l_40,"Runoff Curve Number Data":self.inputs.l_42,
                       "Simulation Period Data":self.inputs.l_60,"Soil Data":self.inputs.l_43,"Soil Layer Data":self.inputs.l_44,
                       "Soil Initial Conditions Data":self.inputs.l_61,"Strip Crop Data":self.inputs.l_45,
                       "Tile Drain Data":self.inputs.l_46,"Watershed Data":self.inputs.l_12,"EI Pct Data":self.inputs.l_50,
                       "STORM TYPE DATA - RFD":self.inputs.l_51,"STORM TYPE DATA - UPDRC":self.inputs.l_52,
                       "Output Options - Global":self.inputs.l_63,"Output Options - AA":self.inputs.l_68,"Output Options - EV":self.inputs.l_69,
                       "Output Options - CSV":self.inputs.l_64,"Output Options - DPP":self.inputs.l_65,
                       "Output Options - NPT":self.inputs.l_66,"Output Options - SIM":self.inputs.l_67,
                       "Output Options - TBL":self.inputs.l_70,"Output Options - MN/MX":self.inputs.l_71,
                       "Output Options - Cell":self.inputs.l_14,"Output Options - Feedlot":self.inputs.l_15,
                       "Output Options - Field Pond":self.inputs.l_16,
                       "Output Options - Classic Gully":self.inputs.l_17,
                       "Output Options - Ephemeral Gully":self.inputs.l_18,
                       "Output Options - Impoundment":self.inputs.l_19,
                       "Output Options - Point Source":self.inputs.l_20,
                       "Output Options - Reach":self.inputs.l_21,
                       "Output Options - Wetland":self.inputs.l_22,
                       "CLIMATE DATA - STATION":self.inputs.l_48,
                       "CLIMATE DATA - DAILY":self.inputs.l_49,"Wetland Data":self.inputs.l_13,"Riparian Buffer Data":self.inputs.l_41,
                       "RUSLE2 Data":self.inputs.l_62,"RiceWQ Data":self.inputs.l_11}
            #Inputs de AnnAGNPS
            for i in load_dict.keys():
                try:
                    load_dict[i].setText(str(retrieve_data(i)))
                except:
                    iface.messageBar().pushMessage("Error Loading Project", "The file you have selected does not have the format or information necessary to upload a project. " ,level=Qgis.Warning, duration=10)
                    return 
            
    def search_document(self,line):
        #Método para elegir en el buscador de archivos el archivo de cada input de AnnAGNPS
        #Este diccionario es para que cuando vaya a seleccionar el archivo le diga exactamente qué archivo tiene que seleccionar
        master_dict = {"AnnAGNPS ID":self.inputs.l_54,"Aquaculture Pond Data":self.inputs.l_2,
                               "Aquaculture Schedule Data":self.inputs.l_24,"Cell Data":self.inputs.l_3,"Classic Gully Data":self.inputs.l_4,
                               "Contour Data":self.inputs.l_25,"Crop Data":self.inputs.l_26,"Crop Growth Data":self.inputs.l_27,
                               "Ephemeral Gully Data":self.inputs.l_5,"Feedlot Data":self.inputs.l_6,"Feedlot Management Data":self.inputs.l_28,
                               "Fertilizer Application Data":self.inputs.l_29,"Fertilizer Reference Data":self.inputs.l_30,
                               "Field Pond Data":self.inputs.l_7,"Geology Data":self.inputs.l_31,
                               "Global Error and Warning Limits Data":self.inputs.l_55,"Global IDs Factors and Flags Data":self.inputs.l_56,
                               "Hydraulic Geometry Data":self.inputs.l_32,"Impoundment Data":self.inputs.l_8,
                               "Irrigation Application Data":self.inputs.l_33,"Management Field Data":self.inputs.l_34,
                               "Management Operation Data":self.inputs.l_35,"Management Schedule Data":self.inputs.l_36,
                               "Non-Crop Data":self.inputs.l_37,
                               "Pesticide Application Data":self.inputs.l_38,"Pesticide Initial Conditions Data":self.inputs.l_57,
                               "Pesticide Reference Data":self.inputs.l_39,"PL Calibration Data":self.inputs.l_58,
                               "Point Source Data":self.inputs.l_9,"RCN Calibration Data":self.inputs.l_59,"Reach Data":self.inputs.l_10,
                               "Reach Nutrient Half-life Data":self.inputs.l_40,"Runoff Curve Number Data":self.inputs.l_42,
                               "Simulation Period Data":self.inputs.l_60,"Soil Data":self.inputs.l_43,"Soil Layer Data":self.inputs.l_44,
                               "Soil Initial Conditions Data":self.inputs.l_61,"Strip Crop Data":self.inputs.l_45,
                               "Tile Drain Data":self.inputs.l_46,"Watershed Data":self.inputs.l_12,"EI Pct Data":self.inputs.l_50,
                               "STORM TYPE DATA - RFD":self.inputs.l_51,"STORM TYPE DATA - UPDRC":self.inputs.l_52,
                               "Output Options - Global":self.inputs.l_63,"Output Options - AA":self.inputs.l_68,"Output Options - EV":self.inputs.l_69,
                               "Output Options - CSV":self.inputs.l_64,"Output Options - DPP":self.inputs.l_65,
                               "Output Options - NPT":self.inputs.l_66,"Output Options - SIM":self.inputs.l_67,
                               "Output Options - TBL":self.inputs.l_70,"Output Options - MN/MX":self.inputs.l_71,
                               "Output Options - Cell":self.inputs.l_14,"Output Options - Feedlot":self.inputs.l_15,
                               "Output Options - Field Pond":self.inputs.l_16,
                               "Output Options - Classic Gully":self.inputs.l_17,
                               "Output Options - Ephemeral Gully":self.inputs.l_18,
                               "Output Options - Impoundment":self.inputs.l_19,
                               "Output Options - Point Source":self.inputs.l_20,
                               "Output Options - Reach":self.inputs.l_21,
                               "Output Options - Wetland":self.inputs.l_22,
                               "CLIMATE DATA - STATION":self.inputs.l_48,
                               "CLIMATE DATA - DAILY":self.inputs.l_49,"Wetland Data":self.inputs.l_13,"Riparian Buffer Data":self.inputs.l_41,
                               "RUSLE2 Data":self.inputs.l_62,"RiceWQ Data":self.inputs.l_11}
        inverted_dic = {value: key for key, value in master_dict.items()}
        #Seleccionar archivo
        fname = QFileDialog.getOpenFileName(self.inputs,f"Select {inverted_dic[line]} file","C/","CSV files (*.csv)")
        #Condiciones en donde si se elige un archivo y la carpeta coincide con la de su sección, solo se pone el nombre del archivo, sino toda la dirección.
        if fname[0]!="":
            if os.path.split(fname[0])[0] == self.dic_folder[line].text():
                line.setText(os.path.split(fname[0])[1])
            else:
                line.setText(fname[0])
        
        #Si se ha elegido antes que los datos provengan de TopAGNPS entonces se quita el check
        dic_search_check = {self.inputs.l_3:self.inputs.checkBox,self.inputs.l_5:self.inputs.checkBox_2,self.inputs.l_10:self.inputs.checkBox_3,self.inputs.l_41:self.inputs.checkBox_4}
        try:
            dic_search_check[line].setChecked(False)
        except:
            pass
    def add_tooltipts(self):
        #Método para añadir los tooltips. La información que aparece cuando pasas el ratón. 
        
        #Poner la información de ayuda de los control files
        #Topagnps
        self.ctopagnps.label.setToolTip(self.tr("Length of a square raster cell of the DEM (resolution) in meters"))
        self.ctopagnps.label_2.setToolTip(self.tr("Number of columns in the DEM input data"))
        self.ctopagnps.label_3.setToolTip(self.tr("Critical Source Area in hectares. \n The default value of “10.0” [ha] will be assumed"))
        self.ctopagnps.label_4.setToolTip(self.tr("This keyword allows the user to specify the whether to produce a warning message and continue execution –or-toproduce an error message and \n terminate execution when the watershed boundary touches the edge of the DEM. \n Optional; the default value of “0” will be assumed.\n 0 = produce warning message and continue execution - (DEFAULT=0, if blank or keyword not used.) \n 1 = produce error message and terminate execution."))
        self.ctopagnps.label_5.setToolTip(self.tr("This keyword allows the user to specify the level of processing from module DEDNM. \n Optional; the default value of “0” will be assumed. \n 0 = full DEM processing - (DEFAULT=0, if blank or keyword not used.) \n 1 = DEM elevation preprocessing only \n 2 = DEM elevation preprocessing and full network generation"))
        self.ctopagnps.label_6.setToolTip(self.tr("This keyword allows the user to specify if the original control file “DNMCNT.INP” is \n to be used to control processing rather than the keywords found in “TopAGNPS.csv”. \n Optional; the default value of “0” will be assumed. \n 0 = do not use the dnmcnt.inp control file - (DEFAULT=0, if blank or keyword not used.) \n 1 = use the dnmcnt.inp control file, if present"))
        self.ctopagnps.label_7.setToolTip(self.tr("This keyword allows the user to specify the input path and filename of input DEM data.\n Optional; the default value of “DEDNM.ASC” will be assumed. (DEFAULT=DEDNM.ASC, if blank or keyword not used.)"))
        self.ctopagnps.label_9.setToolTip(self.tr("This keyword allows the user to specify whether or not to keep the intermediate output \n files produced from DEDNM whose file size is greater than zero. If the control file “TopAGNPS.csv” \n is not used, the default is “1” which will keep the intermediate output files. \n Optional; the default value of “0” (do not keep) will be assumed when the control file “TopAGNPS.csv” is used; \n “1” otherwise. (DEFAULT=0, if blank or keyword not used.)"))
        self.ctopagnps.label_10.setToolTip(self.tr("Minimum Source Channel Length in meters. \n Optional; the default value of “100.0” [m] will be assumed. (DEFAULT=100.0 [m], if blank or keyword not used.)"))
        self.ctopagnps.label_11.setToolTip(self.tr("“nodata” value for input DEM data"))
        self.ctopagnps.label_12.setToolTip(self.tr("This optional keyword allows the user to specify the method of internal loop processing. \n Optional; the default value of “0” (legacy row-major loop processing) will be assumed. \n (DEFAULT=0, if blank or keyword not used; 1= optimize execution using column-major loop processing)."))
        self.ctopagnps.label_14.setToolTip(self.tr("This keyword allows the user to specify if the outlet location is specified by row and \n column coordinates or by UTM coordinates. Optional; the default value of “0” will be assumed. \n 0 = the outlet is specified by row and column - (DEFAULT=0, if blank or keyword not used.) \n 1 = the outlet is specified by UTM x & y coordinates"))
        self.ctopagnps.label_15.setToolTip(self.tr("This keyword allows the user to specify the outlet column or UTM “x” location to use for the channel network.\nOptional if “DEMPROC” = 1 or 2; required if “DEMPROC” = 0."))
        self.ctopagnps.label_17.setToolTip(self.tr("This keyword allows the user to specify the number of outwardly expanding passes to make \n searching for a substitute outlet location. \n Optional; the default value of “2” will be assumed. (DEFAULT=2, if blank or keyword not used; 0 = no snap)"))
        self.ctopagnps.label_18.setToolTip(self.tr("This keyword allows the user to specify the number of rows in the DEM input data"))
        self.ctopagnps.label_19.setToolTip(self.tr("This keyword allows the user to specify the UTM Easting coordinate of the upper left corner of the DEM"))
        self.ctopagnps.label_20.setToolTip(self.tr("This keyword allows the user to specify the UTM Northing coordinate of the upper left corner of the DEM"))
        self.ctopagnps.label_21.setToolTip(self.tr("This keyword allows the user to request extended log messages produced during processing \n to be included in the log file. Optional; the default value of “0” will be assumed. \n 0 = produce more messages - (DEFAULT=0, if blank or keyword not used.) \n 1 = produce less messages"))
        self.ctopagnps.label_22.setToolTip(self.tr("This keyword allows the user to specify the outlet row or UTM “y” location to use for the channel network.\nOptional if “DEMPROC” = 1 or 2; required if “DEMPROC” = 0."))
        #PEG
        self.cpeg.label.setToolTip(self.tr("csv-formatted input file containing PEG point locations to be read in and processed."))
        self.cpeg.label_2.setToolTip(self.tr("Threshold based on a CTI value"))
        self.cpeg.label_3.setToolTip(self.tr("Threshold based on a percent value"))
        #AGBUF
        self.cagbuf.label.setToolTip(self.tr("Name and location of the spatial buffer layer that is to be used"))
        self.cagbuf.label_2.setToolTip(self.tr("Name and location of the spatial vegetation layer that is to be used"))
        self.cagbuf.label_3.setToolTip(self.tr("Value that was assigned as forest in the spatial vegetation layer"))
        self.cagbuf.label_4.setToolTip(self.tr("Value that was assigned as grass in the spatial vegetation layer"))
        self.cagbuf.label_5.setToolTip(self.tr("Threshold value for the cells in number of rasters"))
        self.cagbuf.label_6.setToolTip(self.tr("Threshold value for the reaches"))
        self.cagbuf.label_7.setToolTip(self.tr("Output units, SI or English, for the “AGBUF_AnnAGNPS.csv” file. \n A value of “1” indicates SI units and a value of “0” indicates English units"))
        #AGWET
        self.cagwet.label.setToolTip(self.tr("Name and location of a barrier input file that is to be used for determining barriers and related wetland extents. \n If left blank, then the WIF is invoked"))
        self.cagwet.label_2.setToolTip(self.tr("This optional keyword allows the user to designate a raster grid input file containing buffers. \n Each buffer must have a unique integer ID."))
        self.cagwet.label_3.setToolTip(self.tr("This optional keyword allows the user to designate a raster grid input file containing buffer vegetation values. \n Currently, AGWET only accepts the value of ‘1’ for grass or ‘2’ for forest."))
        self.cagwet.label_4.setToolTip(self.tr("This optional keyword allows the user to designate a raster grid input file containing the buffer zones. \n Currently, AGWET only accepts a value of ‘2’ for all rasters within the buffer zone."))
        self.cagwet.label_5.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the \n spatial files created by DEDNM, RASPRO, RASFOR, and AgFlow are located."))
        self.cagwet.label_6.setToolTip(self.tr("This optional keyword allows the user to specify the path to where any \n csv-formatted input files and the csv-formatted output files created by AGWET will be written."))
        self.cagwet.label_7.setToolTip(self.tr("This optional keyword allows the user to designate a wetness index \n threshold to be used to control the number of points produced by the WIF."))
        self.cagwet.label_8.setToolTip(self.tr("This optional keyword allows the user to designate an erosion index \n threshold value to be used as a criteria to control the number of points produced by the WIF. \n Default = 2.5"))
        self.cagwet.label_9.setToolTip(self.tr("This optional keyword allows the user to designate a drainage area \n threshold in hectares to be used to control the number of points produced by the Wetland Identification Feature (WIF). \n Default = 200.0 [ha]"))
        self.cagwet.label_10.setToolTip(self.tr("This optional keyword allows the user to designate the upper limit that will be used in: \n 1.) Selecting acceptable wetland extents for AnnAGNPS. \n 2.) Determining the barrier height internally. \n Default = 0.02 (2%)"))
        self.cagwet.label_13.setToolTip(self.tr("This optional keyword allows the user to designate the lower limit that will be used in: \n 1.) Selecting acceptable wetland extents for AnnAGNPS. \n 2.) Determining the barrier height internally. \n Default = 0.005 (0.5%)"))
        self.cagwet.label_11.setToolTip(self.tr("This optional keyword allows the user to designate an amount of height in meters to be \n added to the elevation at the barrier-reach point and is used to define the elevation at the top of the barrier. \n This value is used when the “Barrier_Height_Option” is set to use a fixed barrier height value and the wetland \n identification feature (WIF) is used to produce and process barrier points. \n This value must be a positive real number.\n Default = 1.0 [m]"))
        self.cagwet.label_12.setToolTip(self.tr("This optional keyword allows the user to designate an initial and incremental amount of \n height in meters to add when the barrier height is to be determined internally by virtue of the “Barrier_Height_Option” keyword defined below. \n This value must be a positive real number. \n Default = 0.1 [m]"))
        self.cagwet.label_14.setToolTip(self.tr("This optional keyword allows the user to specify a maximum barrier height limit when the \n barrier height is to be determined internally. Iterations determining the barrier height stop when this value is reached. \n This value must be a positive real number greater than the “Barrier_Height_Increment” value. \n Default = 1.0 [m]"))
        self.cagwet.label_15.setToolTip(self.tr("This optional keyword allows the user to designate if a buffer of a userspecified width in \n meters is to be produced around a wetland. If the value is left blank then the global default of one raster \n width will be used for any given barrier point that does not have a buffer width specified."))
        self.cagwet.label_21.setToolTip(self.tr("This optional keyword allows the user to designate if the WIF is used to produce points and \n if those points are to be processed. This keyword, in conjunction with the “Filename” keyword, determines processing"))
        self.cagwet.label_17.setToolTip(self.tr("This optional keyword allows the user to designate whether to use a fixed barrier height value \n using the “Barrier_Height” keyword or to dynamically determine the barrier height internally for all points \n where the barrier height value was not included in the input data file"))
        self.cagwet.label_18.setToolTip(self.tr("This optional keyword allows the user to designate if the wetland extent for a given barrier based \n on elevation is allowed to breach another barrier and wetland extent of a lesser elevation. Options: \n 0 = allow barrier breaching. (Blank defaults to 0) \n 1 = no breaching allowed."))
        self.cagwet.label_19.setToolTip(self.tr("This optional keyword allows the user to select from one of three methods used to produce the buffer \n extent around the wetland. Options: \n 0 = buffers are produced based on the flow path of flow that flows into the buffer and exits into the wetland. \n 1 = buffers are produced around the wetland except for downstream of the barrier. (Blank defaults to 1) \n 2 = buffers are produced completely encompassing the wetland."))
        self.cagwet.label_20.setToolTip(self.tr("This optional keyword allows the user to designate if the LS factor data values, read \n from “AgFlow_LS_Factor.asc”, will be used as the erosion index values or if the erosion index values will be calculated internally. \n This is used to control the number of points produced by the WIF. Options: \n 0 = use “AgFlow_LS_Factor.asc” from AgFlow (Blank defaults to 0) \n 1 = internally calculate the erosion index."))
        #CONCEPTS
        self.cconcepts.label.setToolTip(self.tr("This required keyword allows the user to specify the upstream end reach ID as the \n beginning point of the CONCEPTS corridor. This reach ID value must be a valid AnnAGNPS reach ID. \n If this keyword’s value is left blank then the default that will be used is the reach ID of the reach that \n contains the hydraulically most distant point to the watershed outlet."))
        self.cconcepts.label_2.setToolTip(self.tr("This required keyword allows the user to specify the downstream end reach ID as \n the ending point of the CONCEPTS corridor. This reach ID value must be a valid AnnAGNPS reach ID. \n If this keyword’s value is left blank then the default that will be used is the reach ID of “2” which is the reach flowing into the watershed outlet."))
        #POTHOLE
        self.cpothole.label.setToolTip(self.tr("This optional keyword allows the user to designate if potholes will be identified and processed. \n If this parameter is not present in the control file or if the value for this parameter is blank then the default \n value is 0 meaning that potholes will be identified."))
        self.cpothole.label_2.setToolTip(self.tr("This optional keyword allows the user to designate the minimum area in hectares that is required \n for a pothole to be considered valid and processed for reporting purposes; that is, \n the minimum surface area threshold has been met."))

        #Searcher of documents in AnnAGNPS inputs
        for i in self.dic_lines_search.values():
            i.setToolTip(self.tr("Search document"))
        #Create documents
        for i in self.dic_botones.keys():
            i.setToolTip(self.tr("Create document"))
        
        