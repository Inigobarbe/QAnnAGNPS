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
from PyQt5.QtWidgets import QFrame,QTableWidgetItem,QProgressDialog,QLabel, QLineEdit, QMessageBox,QRadioButton,QCheckBox,QSizePolicy,QSpacerItem
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject
from PyQt5.QtCore import QVariant,QObject, QThread, pyqtSignal, QSize, QThreadPool
from qgis.PyQt import QtWidgets,QtGui, uic
from qgis.utils import iface
from qgis.core import *
from qgis.gui import QgsMapToolEmitPoint,QgsMessageBar
from PyQt5.QtGui import QFont,QColor
from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QProgressBar, QLabel, QWidget, QHBoxLayout, QVBoxLayout
from qgis.core import QgsTask, QgsApplication
from PyQt5.QtGui import QPixmap
from pathlib import Path
import seaborn as sns

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
import sys
import chardet
import glob
import textwrap
import matplotlib.ticker as ticker
import traceback
from scipy.stats import percentileofscore, geom
from scipy import stats
#Local libraries
from .libraries.SALib.sample import saltelli
from .libraries.SALib.analyze import sobol
from .libraries.SALib.sample.morris import sample as sample_morris 
from .libraries.SALib.analyze.morris import analyze as analyze_morris
from .libraries.skopt.optimizer import Optimizer

#Dialog files
from .ui.inputs_dialog import InputsDialog
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
from .ui.table_inputs import TableDialog
from .ui.sensitivity import SensitivityDialog
from .ui.warning_message import warning_message
from .ui.overwrite_project import overwrite_project
from .ui.results_sensitivity import results_sensitivity
from .ui.figure_settings import figure_settings
from .ui.calibration import CalibrationDialog
from .ui.calibration_inputs import calibration_inputs
from .ui.calibration_results import calibration_results
from .ui.fiteval_calibration import fiteval_calibration
from .ui.scenario_analysis import scenario_analysis

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .ui.dialog_base import Dialog_Base
import os.path
import webbrowser
#from .Coordinate_capturer import PrintClickedPoint
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import threading

qgis_processing_lock = threading.Lock()


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
        self.dlg  = Dialog_Base()
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
        self.overwrite = OverwriteDialog()
        self.output = OutputDialog()
        self.existing = ExistingDialog()
        self.documentation = DocumentationDialog()
        self.sensitivity_dialog = SensitivityDialog()
        self.dlg_warning_message = warning_message()
        self.dlg_overwrite_project = overwrite_project()
        self.dlg_results_sensitivity = results_sensitivity()
        self.dlg_figure_settings = figure_settings()
        self.dlg_calibration = CalibrationDialog()
        self.dlg_calibration_inputs = calibration_inputs()
        self.dlg_calibration_results = calibration_results()
        self.dlg_fiteval_calibration= fiteval_calibration()
        self.dlg_scenario_analysis = scenario_analysis()
        
        
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
        #Poner el nombre de las columnas al elegir la capa de suelos y usos
        self.dlg.cbSoil.currentIndexChanged.connect(self.cambios_suelo)
        self.dlg.cbMan.currentIndexChanged.connect(self.cambios_manejo)
        #Para que aparezcan las interfaces donde se pone el nombre de los inputs
        self.dlg.pb_ann.clicked.connect(lambda: (self.inputs.show(), self.inputs.raise_()))
        #Al seleccionar el MDT que se establezca ya el directorio
        self.dlg.comboBox.currentIndexChanged.connect(self.setDirectory)
        
        
        #Folder of executables
        self.executable_directory  = self.plugin_dir+"\\Executables"  
        
        #Quit the warning advice
        self.dlg_warning_message.ok.clicked.connect(self.dlg_warning_message.close)
        
        #Actualizar los control files cuando se le de a uno de los botones
        push_buttons = [self.cgeneral.pushButton,self.cgeneral.pushButton_3,self.cgeneral.pushButton_9,self.cgeneral.pushButton_4,self.cgeneral.pushButton_5,self.cgeneral.pushButton_10,self.cgeneral.pushButton_2,self.cgeneral.pushButton_6,self.cgeneral.pushButton_8,self.cgeneral.pushButton_7]
        for i in push_buttons:
            i.clicked.connect(self.asignar_valores_control_dialogo)
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
        self.agflow.create_csv.clicked.connect(lambda _, b="csv": self.create_control_file_agflow(b))
        self.agflow.create_inp.clicked.connect(lambda _, b="inp": self.create_control_file_agflow(b))
        
        #Seleccionar las capas una vez se hayan seleccionado en el combobox
        self.dlg.comboBox_2.currentIndexChanged.connect(self.instantiate_buffer)
        self.dlg.comboBox_3.currentIndexChanged.connect(self.instantiate_vegetation)
        self.dlg.cbSoil.currentIndexChanged.connect(self.instantiate_soil)
        self.dlg.cbMan.currentIndexChanged.connect(self.instantiate_management)
        
        #Abrir calibracion y sus inputs
        self.dlg.calibration.clicked.connect(self.dlg_calibration.show)
        self.dlg.calibration_results.clicked.connect(self.dlg_calibration_results.show)
        self.dlg_calibration_results.bootstraping.clicked.connect(self.calibration_bootstraping_show)
        self.dlg_calibration.runoff_push.clicked.connect(self.dlg_calibration_inputs.show)
        self.dlg_calibration.erosion_push.clicked.connect(self.dlg_calibration_inputs.show)
        self.dlg_calibration.nitrogen_push.clicked.connect(self.dlg_calibration_inputs.show)
        self.dlg_calibration.carbon_push.clicked.connect(self.dlg_calibration_inputs.show)
        self.dlg_calibration.phosphorus_push.clicked.connect(self.dlg_calibration_inputs.show)
        
        
        #Open scenario analysis
        self.dlg.scenario.clicked.connect(self.dlg_scenario_analysis_show)
        
        #Update graph scenario analysis when date changed
        self.dlg_scenario_analysis.start_date.editingFinished.connect(lambda b=True:self.update_scenario_analysis_graph(b))
        self.dlg_scenario_analysis.end_date.editingFinished.connect(lambda b=True:self.update_scenario_analysis_graph(b))
        
        #Update scenario analysis graph when output changed
        for rb in self.dlg_scenario_analysis.frame_2.findChildren(QRadioButton):
            rb.toggled.connect(lambda _, b=False: self.update_scenario_analysis_graph(b))
        
        #Button to run the scenarios that don´t have the required outptu
        self.dlg_scenario_analysis.execute_scenario.clicked.connect(self.execute_scenario_analysis)
        
        #Fiteval for calibration
        self.dlg_fiteval_calibration.nash.textChanged.connect(self.calibration_bootstraping_update)
        
        
        #Browse calibration inputs
        self.dlg_calibration_inputs.browse.clicked.connect(self.browse_inputs_calibration)
        self.dlg_calibration_inputs.lineEdit.textChanged.connect(self.update_graph_calibration_inputs)
        
        #Browse calibration results
        self.dlg_calibration_results.browse.clicked.connect(self.browse_results_calibration)
        self.dlg_calibration_results.results.textChanged.connect(self.update_graph_calibration_results)
        self.dlg_calibration_results.graph_fit.toggled.connect(lambda checked: self.update_graph_calibration_results() if checked else None)
        self.dlg_calibration_results.one_one.toggled.connect(lambda checked: self.update_graph_calibration_results() if checked else None)
        
        
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
        
        #Se pone la imagen de buscar la carpeta del proyecto y se le da funciones
        self.dlg.button_project.setIcon(QIcon(self.icon_path_search))
        self.dlg.button_project.clicked.connect(self.add_project_folder)
        
        #Se pone la imagen a buscar los inputs de TopAGNPS
        self.dlg.pb_dem.setIcon(QIcon(self.icon_path_search))
        self.dlg.pb_buffer.setIcon(QIcon(self.icon_path_search))
        self.dlg.pb_vegetation.setIcon(QIcon(self.icon_path_search))
        self.dlg.pb_soil.setIcon(QIcon(self.icon_path_search))
        self.dlg.pb_management.setIcon(QIcon(self.icon_path_search))
        
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
        irr_app_col = ["Application_ID","Season_End_Month", "Season_End_Day", "Season_End_Year", "Method_Code", "Water_Source", "Cycle_Duration", "Amount_Lost", "Application_Rate", "Tailwater_Recovery", "Depletion_Lower_Limit", "Application_Amount", "Area_Fraction", "Interval_Number", "Interval_Days", "Chemical_Multiple", "Sediment_Rate", "Depletion_Upper_Limit", "Input_Units_Code"]
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
        soil_initial_col = ["Initial_Soil_Conditions_ID", "Inorganic_N_1" ,"Inorganic_N_2", "Inorganic_P_1","Inorganic_P_2", "Soil_Moisture_1","Soil_Moisture_2", "Organic_Matter_1","Organic_Matter_2","Organic_N_1","Organic_N_2", "Organic_P_1","Organic_P_2", "Surface_Residue", "Mannings_n", "Snow_Depth", "Snow_Density", "Surface_Constant", "Input_Units_Code"]
        rusle2_col = ["RUSLE2_ID","RUSLE2_Filename","RUSLE2_Erosion_Flag"]
        out_global_col =["Glbl_All_V3_csv", "Glbl_All_V3_dpp", "Glbl_All_V3_npt", "Glbl_All_V3_sim", "Glbl_All_V3_txt", "Log_to_File", "Log_to_Screen", "Warning_File", "V1/2_Output_Files", "Reserved", "Glbl_All_Cells", "Glbl_All_Feedlots", "Glbl_All_Fld_Ponds", "Glbl_All_Gullies", "Glbl_All_Pt_Srcs", "Glbl_All_Reaches", "Glbl_All_Impound", "Glbl_All_Wetlands", "Glbl_All_AA_Nutr", "Glbl_All_AA_Pest", "Reserved", "Reserved", "Glbl_All_AA_Sed", "Glbl_All_AA_Wtr", "Glbl_All_EV_Nutr", "Glbl_All_EV_Pest", "Glbl_All_EV_Sed", "Glbl_All_EV_Wtr", "Reserved", "Reserved", "Glbl_All_V2/3_Mass", "Glbl_All_V2/3_Ratio", "Glbl_All_V2/3_UA", "Reserved", "V2_Concepts", "Reserved", "V2_AA", "V2_EV", "V1_AA", "V1_EV"]
        out_csv_col =  ["All_Evt_Lds_Cell_to_DS_Rchs", "All_AA", "All_Events", "All_N", "All_OC", "All_Pesticides", "All_P", "All_Sediment", "All_Water", "AA_N_Ld_Cel_to_DS_Rchs", "AA_N_Ld_in_Rchs", "AA_N_Yld_Cel_to_Rcv_Rch", "AA_OC_Ld_Cel_to_DS_Rchs", "AA_OC_Ld_in_Rchs", "AA_OC_Yld_Cel_to_Rc_v_Rch", "AA_Pest_Ld_Cel_to_DS_Rchs", "AA_Pest_Ld_in_Rchs", "AA_Pest_Yld_Cel_to_Rcv_Rch", "AA_P_Ld_Cel_to_DS_Rchs", "AA_P_Ld_in_Rchs", "AA_P_Yld_Cel_to_Rcv_Rch", "AA_BB_Eros_in_Rch", "AA_BB_Ld_in_DS_Rchs", "AA_Eros_in_Cels", "AA_Gly_Yld_Cel_to_Rcv_Rch", "AA_LS_Eros_in_Cels", "AA_LS_Ld_Cels_to_DS_Rchs", "AA_LS_Ld_in_DS_Rchs", "AA_LS_Yld_Cel_to_Rc_v_Rch", "AA_Rill_Eros_in_Cels", "AA_SR_Yld_Cel_to_Rc_v_Rch", "AA_Wtr_Ld_Cel_to_DS_Rchs", "AA_Wtr_Ld_in_DS_Rc_hs", "AA_Wtr_Yld_Cel_to_Rcv_Rch", "N_Evt_Ld_Cel_to_DS_Rchs", "N_Evt_Ld_in_Rchs", "N_Evt_Yld_Cel_to_Rcv_Rch", "OC_Evt_Ld_Cel_to_DS_Rchs", "OC_Evt_Ld_in_Rchs", "OC_Evt_Yld_Cel_to_Rc_v_Rch", "Pest_Evt_Ld_Cel_to_DS_Rchs", "Pest_Evt_Ld_in_Rchs", "Pest_Evt_Yld_Cel_to_Rcv_Rch", "P_Evt_Ld_Cel_to_DS_Rchs", "P_Evt_Ld_in_Rchs", "P_Evt_Yld_Cel_to_Rcv_Rch", "Sed_Evt_BB_Eros_in_Rch", "Sed_Evt_BB_Ld_in_DS_Rchs", "Sed_Evt_Gly_Eros_in_Cels", "Sed_Evt_Gly_Yld_Cel_to_Rcv_Rch", "Sed_Evt_LS_Eros_in_Cels", "Sed_Evt_LS_Ld_Cel_to_DS_Rchs", "Sed_Evt_LS_Ld_in_Rc_hs", "Sed_Evt_LS_Yld_Cel_to_Rcv_Rch", "Sed_Evt_SR_Eros_in_C_els", "Sed_Evt_SR_Yld_Cel_to_Rcv_Rch", "Wtr_Evt_Ld_Cel_to_DS_Rchs", "Wtr_Evt_Ld_in_DS_Rc_hs", "Wtr_Evt_Pk_Disch_in_DS_Rch", "Wtr_Evt_Yld_Cel_to_Rcv_Rch","Wtr_Evt_Baseflow"]
        out_dpp_col =["Acc_Setup", "Cell_Initial", "Cell_TOC", "Crp_Grwth", "Data_Prep_Pointers", "Weather", "Opr_Rotation", "Pest_Metabolite", "Process_Flag", "Quadrature", "Hydraulic_Geom", "Rch_Routing", "Rch_TOC", "RUSLE_C_Fctr", "RUSLE_C_Fctr_SC", "Canopy_Cover", "Crp_Residue", "Dead_Roots", "PreProc_C_Fctr", "Dom_Contour", "EI_Pcts", "RUSLE_Grwth_Days", "RUSLE_Init_Loc_Oprs", "RUSLE_K_Fctr", "Reserved", "RUSLE_Non-crp_C_Fctr", "RUSLE_Num_SLyr_SR es", "RUSLE_P_Fctr", "RUSLE_P_Fctr_Cntrs", "RUSLE_P_Fctr_Strp", "RUSLE_P_Fctr_Strp_R ot", "RUSLE_Prior_LU", "RUSLE_Res_Coef", "RUSLE_Seg_Res", "RUSLE_Setup_Prd_Seg", "RUSLE_Soil_Moisture", "RUSLE_Surf_Cover", "RUSLE_Surf_Rough", "RUSLE_Unique_Res", "Sed_Part_Distrib", "Seg_EI_Prcp", "Setup_Seg", "Soil_Comp_Surf", "Soil_Comp_Lyrs", "Storm_Types", "Climate_Daily_Wthr", "Eph_Gully_Info", "RUSLE2_Info"]
        out_inver_col = ["AnnAGNPS_ID","Cell","Climate_Station","Contour","Crop","Feedlot","Fertilizer","Mgmt_Seq","Field_Pond","Glbl_Output_Opts","Gully","Hydraulic_Geom","Impoundment","Irrigation","Landuse_Ref","Reserved","Output_Options","Pesticide","Point_Source","Reach","Runoff_Curve_Num","Simulation_Period","Soil_Actual_Surface","Strip_Crop","Tile_Drain","Mgmt_Field","Mgmt_Sched","Mgmt_Opr","Soil_Actual_Layers","Aquaculture_Pond","Aquaculture_Pond_Mg mt_Schd_A","Glbl_Err/Wrn","Soil_Init_Cond","Pest_Init_Cond","Wetland","Riparian_Buffers","RUSLE2"]
        out_sim_col = ["Cell_Components","Conversion_Units","Sht/Rill_Eros_Sed_Yld","Feedlots","Insitu_N_Inorg","Insitu_N_Org","Insitu_Residue","Insitu_OC","Insitu_P_Inorg","Insitu_P_Org","Insitu_Soil_Moist_Daily ","Irrigation","Pesticide_App","Pesticide_Insitu","Gully","Reach_Acc_Mass","Reach_Acc_Ratio","LS_Yld_All_Srcs","Reach_Ld_Nutr","Reserved","Reach_Ld_Sed","Reach_Ld_Wtr","Impound_Routing_A","Reserved","Reach_Routing_Pest","Reach_Routing","Reach_Routing_Wtr","Runoff_Curve_Num","Schd_Oprs","Soil_Part_Distrib","Pond_Release/Yield","Winter_Thermal","Reserved","USLE_Params","Baseflow","Insitu_Soil_Moist_Wsh d_Sum","Wetland_Effects","Pot_ET_Adjust","LS_Rnof_All_Srcs","Riparian_Buffers"]
        out_aa_col = ["Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "AA_Gullies(erosion)", "Reserved", "Reserved", "AA_N_Ld_Mass", "AA_N_Ld_Ratio", "AA_N_Ld_UA", "AA_N_Yld_Mass", "AA_N_Yld_Ratio", "AA_N_Yld_UA", "AA_OC_Ld_Mass", "AA_OC_Ld_Ratio", "AA_OC_Ld_UA", "AA_OC_Yld_Mass", "AA_OC_Yld_Ratio", "AA_OC_Yld_UA", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "Reserved", "AA_P_Ld_Mass", "AA_P_Ld_Ratio", "AA_P_Ld_UA", "AA_P_Yld_Mass", "AA_P_Yld_Ratio", "AA_P_Yld_UA", "Reserved", "Reserved", "Reserved", "AA_Sed_Eros_Mass", "AA_Sed_Eros_Ratio", "AA_Sed_Eros_UA", "AA_Sed_Ld_Mass", "AA_Sed_Ld_Ratio", "AA_Sed_Ld_UA", "AA_Sed_Yld_Mass", "AA_Sed_Yld_Ratio", "AA_Sed_Yld_UA", "AA_Wtr_Ld_Mass", "AA_Wtr_Ld_Ratio", "AA_Wtr_Ld_UA", "AA_Wtr_Yld_Mass", "AA_Wtr_Yld_Ratio", "AA_Wtr_Yld_UA"]
        out_ev_col = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
        out_tbl_col =  ["CCHE1D", "CONCEPTS_XML", "Gaging_Station_Hyd", "REMM", "Gaging_Station_Evt"]
        out_minmax_col = ["Min_Evt_Date","Max_Evt_Date","Max_Number_Evts","Min_Rnof_Evt","Min_Rnof_Cell","Min_Rnof_Outlet","Min_Subarea_ID","Max_Subarea_ID","Subarea_Units_Positn","Max_Vrfy_File_Access","Max_Vrfy_File_Bytes","Input_Units_Code"]
        dic_bc_simulation = {self.inputs.s19:annaid_col,self.inputs.s20:global_error_col,self.inputs.s21:global_ids_col,self.inputs.s22:pesticide_initial_col,self.inputs.s23:pl_calibration_col,self.inputs.s24:rcn_col,self.inputs.s25:sim_col,self.inputs.s26:soil_initial_col,self.inputs.s27:rusle2_col,self.inputs.s28:out_global_col,self.inputs.s29:out_csv_col,self.inputs.s30:out_dpp_col,self.inputs.s31:out_inver_col,self.inputs.s32:out_sim_col,self.inputs.s33:out_aa_col,self.inputs.s34:out_ev_col,self.inputs.s35:out_tbl_col,self.inputs.s36:out_minmax_col}
        #Dictionary csv button - column names
        self.dic_boton_columnas = {**dic_bc_watershed,**dic_bc_general,**dic_bc_climate,**dic_bc_simulation}
        #Dictionary table - column names
        self.table_buttons = [self.inputs.wt1 ,  self.inputs.wt2 ,  self.inputs.wt3 ,  self.inputs.wt4 ,  self.inputs.wt5 ,  self.inputs.wt6 ,  self.inputs.wt7 ,  self.inputs.wt8 ,  self.inputs.wt9 ,  self.inputs.wt10 ,  self.inputs.wt11 ,  self.inputs.wt12 ,  self.inputs.wt13 ,  self.inputs.wt14 ,  self.inputs.wt15 ,  self.inputs.wt16 ,  self.inputs.wt17 ,  self.inputs.wt18 ,  self.inputs.wt19 ,  self.inputs.wt20 ,  self.inputs.wt21 , self.inputs.gt1 ,  self.inputs.gt2 ,  self.inputs.gt3 ,  self.inputs.gt4 ,  self.inputs.gt5 ,  self.inputs.gt6 ,  self.inputs.gt7 ,  self.inputs.gt8 ,  self.inputs.gt9 ,  self.inputs.gt10 ,  self.inputs.gt11 ,  self.inputs.gt12 ,  self.inputs.gt13 ,  self.inputs.gt14 ,  self.inputs.gt15 ,  self.inputs.gt16 ,  self.inputs.gt17 ,  self.inputs.gt18 ,  self.inputs.gt19 ,  self.inputs.gt20 ,  self.inputs.gt21 ,  self.inputs.gt22 ,  self.inputs.gt23 , self.inputs.ct1 ,  self.inputs.ct2 ,  self.inputs.ct3 ,  self.inputs.ct4 ,  self.inputs.ct5 , self.inputs.st1 ,  self.inputs.st2 ,  self.inputs.st3 ,  self.inputs.st4 ,  self.inputs.st5 ,  self.inputs.st6 ,  self.inputs.st7 ,  self.inputs.st8 ,  self.inputs.st9 ,  self.inputs.st10 ,  self.inputs.st11 ,  self.inputs.st12 ,  self.inputs.st13 ,  self.inputs.st14 ,  self.inputs.st15 ,  self.inputs.st16 ,  self.inputs.st17 ,  self.inputs.st18 ]
        self.dic_table_button = {}
        for k,i in enumerate(self.dic_boton_columnas.values()):
            self.dic_table_button[self.table_buttons[k]] = i
        
        #Dictionary of AnnAGNPS input file tables - names of news files
        self.dic_table_filename = {}
        for k,i in enumerate(self.table_buttons):
            self.dic_table_filename[i]=nombres_archivos[k]
            
        #Butons to modify AnnAGNPS inputs with dialog table
        for i in self.dic_table_button.keys():
            i.clicked.connect(lambda _,b=i: self.table_inputs(b))
        self.table_input_overwrite = False
        
        #Dictionary to relate table buttons with lines
        self.dic_line_table = {}
        for k,i in enumerate(self.dic_table_button.keys()):
            self.dic_line_table[i] = list(self.dic_botones.values())[k]
        
        #Change icons of annagnps table inputs
        icon_table = os.path.join(plugin_directory, "images/table.svg")
        for i in self.table_buttons:
            i.setIcon(QIcon(icon_table))
        
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
        self.carpeta_guardar_proyectos = "C:\\Projects_QAnnAGNPS"
        self.dlg.pb_save.clicked.connect(lambda _,b=False: self.save_project(b))
        
        #Boton sobreescribir proyecto
        self.dlg_overwrite_project.yes.clicked.connect(lambda _,b=True: self.save_project(b))
        self.dlg_overwrite_project.yes.clicked.connect(self.dlg_overwrite_project.close)
        
        #Botón para cargar el proyecto
        self.dlg.pb_load.clicked.connect(self.load_project)
        
        #Cargar los proyectos existentes
        self.update_saved_projects(update_scenario = False)
        
        #Diccionario que relaciona cada linea de texto con la carpeta
        self.dic_folder = {self.inputs.l_2:self.inputs.l_1,self.inputs.l_3:self.inputs.l_1,self.inputs.l_4:self.inputs.l_1,self.inputs.l_5:self.inputs.l_1,self.inputs.l_6:self.inputs.l_1,self.inputs.l_7:self.inputs.l_1,self.inputs.l_8:self.inputs.l_1,self.inputs.l_9:self.inputs.l_1,self.inputs.l_10:self.inputs.l_1,self.inputs.l_11:self.inputs.l_1,self.inputs.l_12:self.inputs.l_1,self.inputs.l_13:self.inputs.l_1,self.inputs.l_14:self.inputs.l_1,self.inputs.l_15:self.inputs.l_1,self.inputs.l_16:self.inputs.l_1,self.inputs.l_17:self.inputs.l_1,self.inputs.l_18:self.inputs.l_1,self.inputs.l_19:self.inputs.l_1,self.inputs.l_20:self.inputs.l_1,self.inputs.l_21:self.inputs.l_1,self.inputs.l_22:self.inputs.l_1,self.inputs.l_24:self.inputs.l_23,self.inputs.l_25:self.inputs.l_23,self.inputs.l_26:self.inputs.l_23,self.inputs.l_27:self.inputs.l_23,self.inputs.l_28:self.inputs.l_23,self.inputs.l_29:self.inputs.l_23,self.inputs.l_30:self.inputs.l_23,self.inputs.l_31:self.inputs.l_23,self.inputs.l_32:self.inputs.l_23,self.inputs.l_33:self.inputs.l_23,self.inputs.l_34:self.inputs.l_23,self.inputs.l_35:self.inputs.l_23,self.inputs.l_36:self.inputs.l_23,self.inputs.l_37:self.inputs.l_23,self.inputs.l_38:self.inputs.l_23,self.inputs.l_39:self.inputs.l_23,self.inputs.l_40:self.inputs.l_23,self.inputs.l_41:self.inputs.l_23,self.inputs.l_42:self.inputs.l_23,self.inputs.l_43:self.inputs.l_23,self.inputs.l_44:self.inputs.l_23,self.inputs.l_45:self.inputs.l_23,self.inputs.l_46:self.inputs.l_23,self.inputs.l_48:self.inputs.l_47,self.inputs.l_49:self.inputs.l_47,self.inputs.l_50:self.inputs.l_47,self.inputs.l_51:self.inputs.l_47,self.inputs.l_52:self.inputs.l_47,self.inputs.l_54:self.inputs.l_53,self.inputs.l_55:self.inputs.l_53,self.inputs.l_56:self.inputs.l_53,self.inputs.l_57:self.inputs.l_53,self.inputs.l_58:self.inputs.l_53,self.inputs.l_59:self.inputs.l_53,self.inputs.l_60:self.inputs.l_53,self.inputs.l_61:self.inputs.l_53,self.inputs.l_62:self.inputs.l_53,self.inputs.l_63:self.inputs.l_53,self.inputs.l_64:self.inputs.l_53,self.inputs.l_65:self.inputs.l_53,self.inputs.l_66:self.inputs.l_53,self.inputs.l_67:self.inputs.l_53,self.inputs.l_68:self.inputs.l_53,self.inputs.l_69:self.inputs.l_53,self.inputs.l_70:self.inputs.l_53,self.inputs.l_71:self.inputs.l_53}
        
        #Poner que los inputs que genera topagnps los crea topagnps y que no es necesario decirle la ubicación
        lista = [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3,self.inputs.checkBox_4,self.inputs.checkBox_5]
        for i in lista:
            i.stateChanged.connect(lambda _,b=i: self.topagnps_provided(b))
        
        #Abrir la documentación de los inptus de AnnAGNPS
        self.inputs.pb_doc.clicked.connect(self.documentation.show)
        
        #Poner los tooltips
        self.add_tooltipts()
        
        #Poner las imágenes y condiciones de la página inicial
        self.images_dialog()
        
        #Update sensitivity graph
        radio_buttons = [self.dlg_results_sensitivity.runoff,self.dlg_results_sensitivity.total_erosion,self.dlg_results_sensitivity.gully_erosion,self.dlg_results_sensitivity.pond_erosion,
            self.dlg_results_sensitivity.ephemeral_erosion,self.dlg_results_sensitivity.sheet_erosion,self.dlg_results_sensitivity.nitrogen_erosion,
            self.dlg_results_sensitivity.carbon_erosion,self.dlg_results_sensitivity.phosphorus_erosion]
            
        for radio_button in radio_buttons:
            # Conectar la función solo una vez
            radio_button.toggled.connect(lambda checked, rb=radio_button: self.update_sensitivity_graph_global() if checked else None)
            
        self.dlg_results_sensitivity.radio_morris.toggled.connect(lambda checked: self.update_sensitivity_graph_global() if checked else None)
        self.dlg_results_sensitivity.radio_sobol.toggled.connect(lambda checked: self.update_sensitivity_graph_global() if checked else None)
        self.dlg_results_sensitivity.radio_sensitivity.toggled.connect(lambda checked: self.update_sensitivity_graph_global() if checked else None)
        self.dlg_results_sensitivity.radio_uncertainty.toggled.connect(lambda checked: self.update_sensitivity_graph_global() if checked else None)
        
        #Browse results of sensitivity analysis
        self.dlg_results_sensitivity.browse.clicked.connect(lambda _,b=["Morris",self.dlg_results_sensitivity.radio_morris]: self.browse_files_sensitivity_results(b))
        self.dlg_results_sensitivity.browse_2.clicked.connect(lambda _,b=["Sobol",self.dlg_results_sensitivity.radio_sobol]: self.browse_files_sensitivity_results(b))
        
        
        #When clicking save then close figures settings dialog
        self.dlg_figure_settings.accept.clicked.connect(self.save_figures)
        self.dlg_figure_settings.accept.clicked.connect(self.dlg_figure_settings.close)

        #Ejecutar si se da a OK
        self.dlg.pushButton_6.clicked.connect(self.ejecuciones)
        self.dlg.pushButton_4.clicked.connect(self.ejecuciones)
        
        #Cuando se cierre o ejecute el diálogo que se guarden los índices de los combobox
        self.dlg.finished.connect(self.combo_save)
        
        #Botón para respositorio de github
        self.dlg.pg_github.clicked.connect(self.url_github)
        
        #Botón para llevar al artículo
        self.dlg.article.clicked.connect(self.url_article)
        
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
        
        #Variable para decir si se se ha elegido una carpeta correcta 
        self.file_exist = False
        
        #Función para los outputs de TopAGNPS
        dic = {self.output.pushButton_11:"Cell_raster",self.output.pushButton_13:"Cell_vectorial",self.output.pushButton_14:"Boundary_raster",self.output.pushButton_19:"Boundary_vectorial",self.output.pushButton_22:"Reaches_raster",self.output.pushButton_20:"Reaches_vectorial",self.output.pushButton_21:"Accumulated",self.output.pushButton_23:"Terrain_slope",self.output.pushButton_24:"Hydraulic",self.output.pushButton_25:"Terrain_aspect",self.output.pushButton_26:"RUSLE",self.output.pushButton_27:"Longest_raster",self.output.pushButton_28:"Longest_vectorial",self.output.pushButton_29:"PEG_points"}
        for i in dic.keys():
            i.clicked.connect(lambda _,b = dic[i]:self.output_topagnps(b))
            
        #Open sensitivity analysis dialog and results
        self.dlg.sensitivity.clicked.connect(self.sensitivity_dialog.show)
        self.dlg.results_sensitivity.clicked.connect(self.dlg_results_sensitivity.show)
        
        #Show inputs in sensitivity analysis dialog
        self.sensitivity_dialog.Spatial.clicked.connect(lambda _,b = "Spatial":self.annagnps_inputs(b))
        self.sensitivity_dialog.Watershed.clicked.connect(lambda _,b = "Watershed":self.annagnps_inputs(b))
        self.sensitivity_dialog.General.clicked.connect(lambda _,b = "General":self.annagnps_inputs(b))
        self.sensitivity_dialog.Climate.clicked.connect(lambda _,b = "Climate":self.annagnps_inputs(b))
        self.sensitivity_dialog.Simulation.clicked.connect(lambda _,b = "Simulation":self.annagnps_inputs(b))
        
        #Show inputs in sensitivity analysis dialog
        self.dlg_calibration.Spatial.clicked.connect(lambda _,b = "Spatial":self.calibration_inputs(b))
        self.dlg_calibration.Watershed.clicked.connect(lambda _,b = "Watershed":self.calibration_inputs(b))
        self.dlg_calibration.General.clicked.connect(lambda _,b = "General":self.calibration_inputs(b))
        self.dlg_calibration.Climate.clicked.connect(lambda _,b = "Climate":self.calibration_inputs(b))
        self.dlg_calibration.Simulation.clicked.connect(lambda _,b = "Simulation":self.calibration_inputs(b))
        
        #Add distributions to combobox
        self.sensitivity_dialog.distributions.addItems(["Uniform","Logaritmic uniform","Triangular","Normal","Lognormal","Normal truncated"])
        
        #Button to add information to the sensitivity table and calibration
        self.sensitivity_dialog.add.clicked.connect(self.add_sensitivity_table)
        self.dlg_calibration.add.clicked.connect(self.add_calibration_table)
        
        #Button to delete information of the sensitivity table and calibration
        self.sensitivity_dialog.delete_row.clicked.connect(self.delete_sensitivity_table)
        self.dlg_calibration.delete_row.clicked.connect(self.delete_calibration_table)
        
        #Run sensitivity analysis and calibration
        self.sensitivity_dialog.accept.clicked.connect(self.run_sensitivity_analysis)
        self.dlg_calibration.accept.clicked.connect(self.run_calibration)
        
        #Por defecto, cuando se sobreescribe se sobreescibe con el CSV no con la tabla del diálogo
        self.overwriting_input =False
        
        #Search inputs in sensitivity analysis and calibration
        self.sensitivity_dialog.search.textChanged.connect(self.search_sensitiviy_input)
        self.dlg_calibration.search.textChanged.connect(self.search_calibration_input)
        
        #Diccionario analisis de sensibilidad nombre en el dialogo - [nombre del archivo, nombre de la columna]
        dic_spatial = {'Pixel Size':['Spatial','TOPAGNPS.csv','FILENAME'],'Critical Source Area':['Spatial','TOPAGNPS.csv','CSA'],'Minimum Source Channel \nLength':['Spatial','TOPAGNPS.csv','MSCL'],'Absolute CTI':['Spatial','PEG.csv','CTI_value'],'Relative CTI':['Spatial','PEG.csv','Accum_pct'],'Cell Threshold':['Spatial','AGBUF.csv','C_THRESHOLD'],'Reach Threshold':['Spatial','AGBUF.csv','R_THRESHOLD'],'Drainage area \nto concentrated flow':['Spatial','AGFLOW.csv','Area'],'Maximum profile length \nuntil deposition':['Spatial','AGFLOW.csv','Length'],'Maximum Profile Slope':['Spatial','AGFLOW.csv','MxSlope'],'Wetness Index Threshold':['Spatial','AGWET.csv','WI_Threshold'],'Erosion Index Threshold':['Spatial','AGWET.csv','Erosion_Index_Threshold'],'Drainage Area Threshold':['Spatial','AGWET.csv','DA_Threshold'],'Maximum Wetland Ratio':['Spatial','AGWET.csv','Max_Wetland_Ratio'],'Minimum Wetland Ratio':['Spatial','AGWET.csv','Min_Wetland_Ratio'],'Barrier Height':['Spatial','AGWET.csv','Barrier_Height'],'Barrier Height Increment':['Spatial','AGWET.csv','Barrier_Height_Increment'],'Barrier Height Maximum':['Spatial','AGWET.csv','Barrier_Height_Max'],'Buffer width':['Spatial','AGWET.csv','Buffer_Width'],'Pothole Surface Area':['Spatial','POTHOLE.csv','POTHOLE_SURFACE_AREA']}
        dic_watershed = {'Pond area':[self.inputs.l_2,'Pond_Area'],'Pond Depth':[self.inputs.l_2,'Pond_Depth'],'Seepage Rate':[self.inputs.l_2,'Seepage_Rate'],'Sediment Delivery Ratio Pond':[self.inputs.l_2,'Sediment_Delivery_Ratio'],'Organic Carbon \nCalibration Factor Pond':[self.inputs.l_2,'OC_Calib_Fctr'],'Nitrogen Calibration Factor Pond':[self.inputs.l_2,'N_Calib_Fctr'],'Phosphorus Calibration Factor Pond':[self.inputs.l_2,'P_Calib_Fctr'],'Erosion Calibration Factor Pond':[self.inputs.l_2,'Erosion_Calib_Fctr'],'Sheet flow Manning’s n':[self.inputs.l_3,'Sheet_Flow_Mannings_n'],'Concentrated flow \nhydraulic depth':[self.inputs.l_3,'Conc_Flow_Hydraulic_Depth'],'Concentrated flow Manning’s n':[self.inputs.l_3,'Conc_Flow_Mannings_n'],'Delivery Ratio Pond':[self.inputs.l_3,'Delivery_Ratio'],'Constant USLE C factor':[self.inputs.l_3,'Constant_USLE_C_Fctr'],'Constant USLE P factor':[self.inputs.l_3,'Constant_USLE_P_Fctr'],'All Organic Carbon \nCalibration Factor':[self.inputs.l_3,'All_OC_Calib_Fctr'],'All Nitrogen Calibration Factor':[self.inputs.l_3,'All_N_Calib_Fctr'],'All Phosphorus Calibration Factor':[self.inputs.l_3,'All_P_Calib_Fctr'],'Sheet and Rill Erosion \nCalibration Factor':[self.inputs.l_3,'Sheet_and_Rill_Erosion_Calib_Fctr'],'Gullies Erosion Calibration Factor':[self.inputs.l_3,'Gullies_Erosion_Calib_Fctr'],'Head Cut Depth':[self.inputs.l_4,'Headcut_Depth'],'Erosion Coefficient':[self.inputs.l_4,'Erosion_Coef'],'Erosion Exponent':[self.inputs.l_4,'Erosion_exp'],'Delivery Ratio Gully':[self.inputs.l_4,'Delivery_Ratio'],'Organic Carbon \nCalibration Factor Gully':[self.inputs.l_4,'OC_Calib_Fctr'],'Nitrogen Calibration Factor Gully':[self.inputs.l_4,'N_Calib_Fctr'],'Phosphorus Calibration Factor Gully':[self.inputs.l_4,'P_Calib_Fctr'],'Erosion Calibration Factor Gully':[self.inputs.l_4,'Erosion_Calib_Fctr'],'Critical Shear Stress \nEphemeral Gully':[self.inputs.l_5,'Critical_Shear_Stress'],'Erosion Depth':[self.inputs.l_5,'Erosion_Depth'],'Delivery Ratio Ephemeral Gully':[self.inputs.l_5,'Delivery_Ratio'],'Manning’s n Ephemeral Gully':[self.inputs.l_5,'Mannings_n'],'Re Plant Period':[self.inputs.l_5,'Replant_Period'],'Organic Carbon':[self.inputs.l_5,'OC_Calib_Fctr'],'Nitrogen':[self.inputs.l_5,'N_Calib_Fctr'],'Phosphorus':[self.inputs.l_5,'P_Calib_Fctr'],'Erosion':[self.inputs.l_5,'Erosion_Calib_Fctr'],'Headcut detachment leading \ncoefficient a':[self.inputs.l_5,'Headcut_Dtach/Erod_Coef_a'],'Headcut erodibility \nleading coefficient a':[self.inputs.l_5,'Headcut_Dtach/Erod_Coef_a'],'Headcut detachment exponent \ncoefficient b':[self.inputs.l_5,'Headcut_Dtach/Erod_Exp_Coef_b'],'Headcut erodibility exponent \ncoefficient b':[self.inputs.l_5,'Headcut_Dtach/Erod_Exp_Coef_b'],'Maximum Buffer Trapping \nEfficiency TE m':[self.inputs.l_5,'Max_Trapping_Efficiency'],'Open Area':[self.inputs.l_6,'Open_Area'],'Paved Ratio':[self.inputs.l_6,'Paved_Ratio'],'Roof Area':[self.inputs.l_6,'Roof_Area'],'Upslope Area':[self.inputs.l_6,'Upslope_Area'],'Feedlot Initial N':[self.inputs.l_6,'Initial_N'],'Feedlot Initial P':[self.inputs.l_6,'Initial_P'],'Feedlot Initial OrgC':[self.inputs.l_6,'Initial_OC'],'Delta N':[self.inputs.l_6,'Delta_N'],'Delta P':[self.inputs.l_6,'Delta_P'],'Delta OrgC':[self.inputs.l_6,'Delta_OC'],'Feedlot Max N':[self.inputs.l_6,'Max_N'],'Feedlot Max P':[self.inputs.l_6,'Max_P'],'Feedlot Max OrgC':[self.inputs.l_6,'Max_OC'],'Feedlot Pack N':[self.inputs.l_6,'Pack_N'],'Feedlot Pack P':[self.inputs.l_6,'Pack_P'],'Feedlot Pack OrgC':[self.inputs.l_6,'Pack_OC'],'Organic Carbon Calibration \nFactor Feedlot':[self.inputs.l_6,'OC_Calib_Fctr'],'Nitrogen Calibration \nFactor Feedlot':[self.inputs.l_6,'N_Calib_Fctr'],'Phosphorus Calibration \nFactor Feedlot':[self.inputs.l_6,'P_Calib_Fct'],'Erosion Calibration \nFactor Feedlot':[self.inputs.l_6,'Erosion_Calib_Fctr'],'Cell Buffer Length':[self.inputs.l_6,'Cell_Buffer_Length'],'Field Pond area':[self.inputs.l_7,'Pond_Area'],'Number of rotation years':[self.inputs.l_7,'Number_of_Rotation_Years'],'Number gate operations':[self.inputs.l_7,'Number_of_Gate_Operations'],'Delivery Ratio Field Pond':[self.inputs.l_7,'Delivery_Ratio'],'Volume of release water':[self.inputs.l_7,'Volume_of_Release_Water'],'Drain Time':[self.inputs.l_7,'Drain_Time'],'Release rate':[self.inputs.l_7,'Release_Rate'],'Sediment Concentration':[self.inputs.l_7,'Sediment_Conc'],'Clay content Field Pond':[self.inputs.l_7,'Clay_Content'],'Silt content Field Pond':[self.inputs.l_7,'Silt_Content'],'Organic Carbon Calibration Factor Field Pond':[self.inputs.l_7,'OC_Calib_Fctr'],'Nitrogen Calibration Factor Field Pond':[self.inputs.l_7,'N_Calib_Fctr'],'Phosphorus Calibration Factor Field Pond':[self.inputs.l_7,'P_Calib_Fctr'],'Erosion Calibration Factor Field Pond':[self.inputs.l_7,'Erosion_Calib_Fctr'],'Impoundment Infiltration':[self.inputs.l_8,'Infiltration'],'Impoundment Seepage':[self.inputs.l_8,'Seepage'],'Permanent Pool Depth':[self.inputs.l_8,'Permanent_Pool_Depth'],'Impound Volume Coefficient':[self.inputs.l_8,'Volume_Coef'],'Impound Volume Exponent':[self.inputs.l_8,'Volume_Exp'],'Impound Discharge Coefficient':[self.inputs.l_8,'Discharge_Coef'],'Impound Discharge Exponent':[self.inputs.l_8,'Discharge_Exp'],'Sediment Clean Out Depth':[self.inputs.l_8,'Sed_Clean_Out_Depth'],'Sediment Clean Out Year':[self.inputs.l_8,'Sed_Clean_Out_Year'],'Point Flow':[self.inputs.l_9,'Point_Flow'],'Point Nitrogen':[self.inputs.l_9,'Point_N'],'Point Phosphorus':[self.inputs.l_9,'Point_P'],'Point Organic Carbon':[self.inputs.l_9,'Point_OC'],'Organic Carbon Calibration Factor':[self.inputs.l_9,'OC_Calib_Fctr'],'Nitrogen Calibration Factor':[self.inputs.l_9,'N_Calib_Fctr'],'Phosphorus Calibration Factor':[self.inputs.l_9,'P_Calib_Fctr'],'Erosion Calibration Factor':[self.inputs.l_9,'Erosion_Calib_Fctr'],'Reach Manning’s n':[self.inputs.l_10,'Mannings_n'],'Reach Flow Depth':[self.inputs.l_10,'Flow_Depth'],'Valley Width':[self.inputs.l_10,'Valley_Width'],'Valley n':[self.inputs.l_10,'Valley_Mannings_n'],'Delivery Ratio Reach':[self.inputs.l_10,'Delivery_Ratio'],'Latitude':[self.inputs.l_12,'Latitude'],'Longitude':[self.inputs.l_12,'Longitude'],'Wetland Area':[self.inputs.l_13,'Wetland_Area'],'Initial Water Depth':[self.inputs.l_13,'Initial_Water_Depth'],'Minimum Water Depth':[self.inputs.l_13,'Min_Water_Depth'],'Maximum Water Depth':[self.inputs.l_13,'Max_Water_Depth'],'Water Temperature':[self.inputs.l_13,'Water_Temperature'],'Potential Daily Infiltration':[self.inputs.l_13,'Potential_Daily_Infiltration'],'Weir Coefficient':[self.inputs.l_13,'Weir_Coef'],'Weir Width':[self.inputs.l_13,'Weir_Width'],'Weir Height':[self.inputs.l_13,'Weir_Height'],'Soluble N Concentration':[self.inputs.l_13,'Soluble_N_Conc'],'Nitrate Loss Rate':[self.inputs.l_13,'Nitrate-N_Loss_Rate'],'Nitrate Loss Rate Coefficient':[self.inputs.l_13,'Nitrate-N_Loss_Rate_Coef'],'Temperature Coefficient':[self.inputs.l_13,'Temperature_Coef'],'Weir Exponent':[self.inputs.l_13,'Weir_Exp']}
        dic_general = {'Maximum Pool Depth':[self.inputs.l_24,'Max_Pool_Depth'],'Minimum Pool Depth':[self.inputs.l_24,'Min_Pool_Depth'],'Fill/Release Volume':[self.inputs.l_24,'Fill/Release_Vol'],'Fill/Drain Time':[self.inputs.l_24,'Fill/Drain_Time'],'Fill/Release Rate':[self.inputs.l_24,'Fill/Release_Rate'],'Fill/Drain All':[self.inputs.l_24,'Fill/Drain_All_Code'],'Total Sediment Concentration':[self.inputs.l_24,'Total_Sed_Conc'],'Clay Content Pond Schedule':[self.inputs.l_24,'Clay_Content'],'Silt Content Pond Schedule':[self.inputs.l_24,'Silt_Content'],'Total Nitrogen':[self.inputs.l_24,'Total_N'],'Dissolved Nitrogen':[self.inputs.l_24,'Dissolved_N'],'Total Phosphorus':[self.inputs.l_24,'Total_P'],'Dissolved Phosphorus':[self.inputs.l_24,'Dissolved_P'],'Sediment Concentration—Winter':[self.inputs.l_24,'Sed_Conc_Winter'],'Total Nitrogen—Winter':[self.inputs.l_24,'Total_N_Winter'],'Dissolved Nitrogen—Winter':[self.inputs.l_24,'Dissolved_N_Winter'],'Total Phosphorus—Winter':[self.inputs.l_24,'Total_P_Winter'],'Dissolved Phosphorus—Winter':[self.inputs.l_24,'Dissolved_P_Winter'],'Sediment Concentration—Spring':[self.inputs.l_24,'Sed_Conc_Spring'],'Total Nitrogen—Spring':[self.inputs.l_24,'Total_N_Spring'],'Dissolved Nitrogen—Spring':[self.inputs.l_24,'Dissolved_N_Spring'],'Total Phosphorus—Spring':[self.inputs.l_24,'Total_P_Spring'],'Dissolved Phosphorus—Spring':[self.inputs.l_24,'Dissolved_P_Spring'],'Sediment Concentration—Summer':[self.inputs.l_24,'Sed_Conc_Summer'],'Total Nitrogen—Summer':[self.inputs.l_24,'Total_N_Summer'],'Dissolved Nitrogen—Summer':[self.inputs.l_24,'Dissolved_N_Summer'],'Total Phosphorus—Summer':[self.inputs.l_24,'Total_P_Summer'],'Dissolved Phosphorus—Summer':[self.inputs.l_24,'Dissolved_P_Summer'],'Sediment Concentration—Autumn':[self.inputs.l_24,'Sed_Conc_Autumn'],'Total Nitrogen—Autumn':[self.inputs.l_24,'Total_N_Autumn'],'Dissolved Nitrogen—Autumn':[self.inputs.l_24,'Dissolved_N_Autumn'],'Total Phosphorus—Autumn':[self.inputs.l_24,'Total_P_Autumn'],'Dissolved Phosphorus—Autumn':[self.inputs.l_24,'Dissolved_P_Autumn'],'Furrow Slope':[self.inputs.l_25,'Furrow_Slope'],'Yield Units Harvested per Area':[self.inputs.l_26,'Yield_Units_Harvested'],'Residue Mass Ratio':[self.inputs.l_26,'Residue_Mass_Ratio'],'Surface decomposition Crop':[self.inputs.l_26,'Surface_Decomp'],'Sub-surface decomposition Crop':[self.inputs.l_26,'Subsurface_Decomp'],'USLE C-Factor Crop':[self.inputs.l_26,'USLE_C_Fctr'],'Moisture Depletion':[self.inputs.l_26,'Moisture_Depletion'],'Crop Residue_30%':[self.inputs.l_26,'Crop_Residue_30%'],'Crop Residue_60%':[self.inputs.l_26,'Crop_Residue_60%'],'Crop Residue_90%':[self.inputs.l_26,'Crop_Residue_90%'],'Yield Unit Mass':[self.inputs.l_26,'Yield_Unit_Mass'],'Harvest C-N Ratio':[self.inputs.l_26,'Harvest_CN_Ratio'],'N Uptake':[self.inputs.l_26,'N_Uptake'],'P Uptake':[self.inputs.l_26,'P_Uptake'],'Harvest C-P Ratio':[self.inputs.l_26,'Harvest_CP_Ratio'],'Growth Time Ini':[self.inputs.l_26,'Growth_Time_Ini'],'Growth Time Dev':[self.inputs.l_26,'Growth_Time_Dev'],'Growth Time Mat':[self.inputs.l_26,'Growth_Time_Mat'],'Basal Crop Coefficient (“Kcb-ini”) crop':[self.inputs.l_26,'Basal_Crop_Coef_Ini'],'Basal Crop Coefficient (“Kcb-mid”) crop':[self.inputs.l_26,'Basal_Crop_Coef_Mid'],'Basal Crop Coefficient (“Kcb-end”) crop':[self.inputs.l_26,'Basal_Crop_Coef_End'],'Root Mass':[self.inputs.l_27,'Root_Mass'],'Canopy Cover':[self.inputs.l_27,'Canopy_Cover'],'Rain Fall Height':[self.inputs.l_27,'Rain_Fall_Height'],'Pack Remove Ratio':[self.inputs.l_28,'Pack_Remove_Ratio'],'Pack Start N':[self.inputs.l_28,'Pack_Start_N'],'Pack Start P':[self.inputs.l_28,'Pack_Start_P'],'Pack Start OrgC':[self.inputs.l_28,'Pack_Start_OC'],'Pack Change N':[self.inputs.l_28,'Pack_Change_N'],'Pack Change P':[self.inputs.l_28,'Pack_Change_P'],'Pack Change OrgC':[self.inputs.l_28,'Pack_Change_OC'],'Fertilizer Rate':[self.inputs.l_29,'Application_Rate'],'Fertilizer Inorganic N':[self.inputs.l_30,'Inorganic_N'],'Fertilizer Organic N':[self.inputs.l_30,'Organic_N'],'Fertilizer Inorganic P':[self.inputs.l_30,'Inorganic_P'],'Fertilizer Organic P':[self.inputs.l_30,'Organic_P'],'Fertilizer Organic Matter':[self.inputs.l_30,'Organic_Matter'],'Delay Time':[self.inputs.l_31,'Delay_Time'],'Water Table':[self.inputs.l_31,'Water_Table'],'Aquifer Saturated \nHydraulic Conductivity':[self.inputs.l_31,'Aquifer_Sat_Hyd_Conduct'],'K-vadose Saturated \nHydraulic Conductivity':[self.inputs.l_31,'Vadose_Sat_Hyd_Conduct'],'Aquifer Porosity':[self.inputs.l_31,'Porosity'],'Aquifer Field Capacity':[self.inputs.l_31,'Field_Capacity'],'Aquifer Specific Yield':[self.inputs.l_31,'Specific_Yield'],'Aquifer Thickness':[self.inputs.l_31,'Thickness'],'Aquifer Soluble Nitrogen':[self.inputs.l_31,'Soluble_N'],'Aquifer Soluble Phosphorus':[self.inputs.l_31,'Soluble_P'],'Channel Length Coefficient':[self.inputs.l_32,'Channel_Length_Coef'],'Channel Length Exponent':[self.inputs.l_32,'Channel_Length_Exp'],'Channel Width Coefficient':[self.inputs.l_32,'Channel_Width_Coef'],'Channel Width Exponent':[self.inputs.l_32,'Channel_Width_Exp'],'Channel Depth Coefficient':[self.inputs.l_32,'Channel_Depth_Coef'],'Channel Depth Exponent':[self.inputs.l_32,'Channel_Depth_Exp'],'Valley Width Coefficient':[self.inputs.l_32,'Valley_Width_Coef'],'Valley Width Exponent':[self.inputs.l_32,'Valley_Width_Exp'],'Cycle Duration':[self.inputs.l_33,'Cycle_Duration'],'Amount Lost':[self.inputs.l_33,'Amount_Lost'],'Application Rate':[self.inputs.l_33,'Application_Rate'],'Tailwater Recovery':[self.inputs.l_33,'Tailwater_Recovery'],'Depletion Lower Limit':[self.inputs.l_33,'Depletion_Lower_Limit'],'Application Amount':[self.inputs.l_33,'Application_Amount'],'Area Fraction':[self.inputs.l_33,'Area_Fraction'],'Interval Number':[self.inputs.l_33,'Interval_Number'],'Interval Days':[self.inputs.l_33,'Interval_Days'],'Chemical Multiple':[self.inputs.l_33,'Chemical_Multiple'],'Sediment Rate':[self.inputs.l_33,'Sediment_Rate'],'Depletion Upper Limit':[self.inputs.l_33,'Depletion_Upper_Limit'],'Percent Rock Cover':[self.inputs.l_34,'Percent_Rock_Cover'],'Random Roughness':[self.inputs.l_34,'Random_Roughness'],'Terrace Horizontal Distance':[self.inputs.l_34,'Terrace_Horizontal_Distance'],'Terrace grade':[self.inputs.l_34,'Terrace_Grade'],'Residue Cover Remaining':[self.inputs.l_35,'Residue_Cover_Remaining'],'Residue Weight Remaining':[self.inputs.l_35,'Residue_Weight_Remaining'],'Area Disturbed':[self.inputs.l_35,'Area_Disturbed'],'Initial Random Roughness':[self.inputs.l_35,'Initial_Random_Roughness'],'Final Random Roughness':[self.inputs.l_35,'Final_Random_Roughness'],'Operation Tillage Depth':[self.inputs.l_35,'Operation_Tillage_Depth'],'Added Surface Residue':[self.inputs.l_35,'Added_Surface_Residue'],'Surface Decomposition \nmanagement':[self.inputs.l_35,'Surface_Decomp'],'Sub-surface Decomposition \nmanagement':[self.inputs.l_35,'Subsurface_Decomp'],'Surface Residue_30%':[self.inputs.l_35,'Surface_Residue_30%'],'Surface Residue_60%':[self.inputs.l_35,'Surface_Residue_60%'],'Surface Residue_90%':[self.inputs.l_35,'Surface_Residue_90%'],'Post Event Manning’s n':[self.inputs.l_36,'Post_Event_Mannings_n'],'Post Event Surface Constant':[self.inputs.l_36,'Post_Event_Surface_Constant'],'Operation Residue Change':[self.inputs.l_36,'Operation_Residue_Change'],'Tile Drain Controlled Depth':[self.inputs.l_36,'Tile_Drain_Controlled_Depth'],'Annual Root Mass':[self.inputs.l_37,'Annual_Root_Mass'],'Annual Cover Ratio':[self.inputs.l_37,'Annual_Cover_Ratio'],'Annual Rain Fall Height':[self.inputs.l_37,'Annual_Rain_Fall_Height'],'Surface Residue Cover':[self.inputs.l_37,'Surface_Cover_Residue'],'USLE C-Factor Non Crop':[self.inputs.l_37,'USLE_C-Fctr'],'Basal Crop Coefficient (“Kcb-mid”) Non Crop':[self.inputs.l_37,'Basal_Crop_Coef_Mid'],'Pesticide Rate':[self.inputs.l_38,'Application_Rate'],'Pesticide Depth':[self.inputs.l_38,'Depth'],'Pesticide Foliage Fraction':[self.inputs.l_38,'Foliage_Fraction'],'Pesticide Soil Fraction':[self.inputs.l_38,'Soil_Fraction'],'Pesticide Solubility':[self.inputs.l_39,'Solubility'],'Pesticide Partition':[self.inputs.l_39,'Partition'],'Pesticide Soil Half-life':[self.inputs.l_39,'Soil_Half-life'],'Pesticide Foliage Half-life':[self.inputs.l_39,'Foliage_Halflife'],'Pesticide Washoff':[self.inputs.l_39,'Washoff'],'Metabolite Transformation':[self.inputs.l_39,'Metabolite_Transformation'],'Pesticide Reach Half-life':[self.inputs.l_39,'Reach_Halflife'],'Reach Nitrogen Half-life':[self.inputs.l_40,'N_Half-life'],'Reach Phosphorus Half-life':[self.inputs.l_40,'P_Half-life'],'Reach Organic Carbon Half-life':[self.inputs.l_40,'OC_Half-life'],'Slope':[self.inputs.l_41,'Buffer_Slope'],'Maximum Trapping \nEfficiency “TE-m”':[self.inputs.l_41,'Max_Trap_Efficiency'],'Effective Buffer Width':[self.inputs.l_41,'Eff_Wdth_Thru_Buffer'],'Effective Concentrated \nFlow Width':[self.inputs.l_41,'Eff_Wdth_Along_Buffer'],'Drainage Area to Upstream \nPortion of Buffer':[self.inputs.l_41,'Drainage_Area_to_Buffer'],'Actual Trapping Efficiency \n“TE-a” Clay':[self.inputs.l_41,'Actual_Trap_Efficiency_Clay'],'Actual Trapping Efficiency \n“TE-a” Silt':[self.inputs.l_41,'Actual_Trap_Efficiency_Silt'],'Actual Trapping Efficiency \n“TE-a” Sand':[self.inputs.l_41,'Actual_Trap_Efficiency_Sand'],'Actual Trapping Efficiency \n“TE-a” Sm Agg':[self.inputs.l_41,'Actual_Trap_Efficiency_Sm_Agg'],'Actual Trapping Efficiency \n“TE-a” Lg Agg':[self.inputs.l_41,'Actual_Trap_Efficiency_Lg_Agg'],'Fraction Trapped “TE-ps” Clay':[self.inputs.l_41,'Fraction_Trapped_Clay'],'Fraction Trapped “TE-ps” Silt':[self.inputs.l_41,'Fraction_Trapped_Silt'],'Fraction Trapped “TE-ps” Sand':[self.inputs.l_41,'Fraction_Trapped_Sand'],'Fraction Trapped “TE-ps” Sm Agg':[self.inputs.l_41,'Fraction_Trapped_Sm_Agg'],'Fraction Trapped “TE-ps” Lg Agg':[self.inputs.l_41,'Fraction_Trapped_Lg_Agg'],'Curve Number “A”':[self.inputs.l_42,'CN_A'],'Curve Number “B”':[self.inputs.l_42,'CN_B'],'Curve Number “C”':[self.inputs.l_42,'CN_C'],'Curve Number “D”':[self.inputs.l_42,'CN_D'],'K-factor':[self.inputs.l_43,'K_Factor'],'Albedo':[self.inputs.l_43,'Albedo'],'Time to consolidation':[self.inputs.l_43,'Time_to_Consolidation'],'Impervious Depth':[self.inputs.l_43,'Impervious_Depth'],'Specific Gravity':[self.inputs.l_43,'Specific_Gravity'],'Layer Depth':[self.inputs.l_44,'Layer_Depth'],'Bulk Density':[self.inputs.l_44,'Bulk_Density'],'Clay Ratio':[self.inputs.l_44,'Clay_Ratio'],'Silt Ratio':[self.inputs.l_44,'Silt_Ratio'],'Sand Ratio':[self.inputs.l_44,'Sand_Ratio'],'Rock Ratio':[self.inputs.l_44,'Rock_Ratio'],'Very Fine Sand Ratio':[self.inputs.l_44,'Very_Fine_Sand_Ratio'],'CaCO3':[self.inputs.l_44,'CaCO3_Content'],'Saturated Conductivity':[self.inputs.l_44,'Saturated_Conductivity'],'Field Capacity':[self.inputs.l_44,'Field_Capacity'],'Wilting Point':[self.inputs.l_44,'Wilting_Point'],'Base Saturation':[self.inputs.l_44,'Base_Saturation'],'Unstable Aggregate Ratio':[self.inputs.l_44,'Unstable_Aggregate_Ratio'],'pH':[self.inputs.l_44,'pH'],'Organic Matter Ratio':[self.inputs.l_44,'Organic_Matter_Ratio'],'Organic N Ratio':[self.inputs.l_44,'Organic_N_Ratio'],'Inorganic N Ratio':[self.inputs.l_44,'Inorganic_N_Ratio'],'Organic P Ratio':[self.inputs.l_44,'Organic_P_Ratio'],'Inorganic P Ratio':[self.inputs.l_44,'Inorganic_P_Ratio'],'P Factor':[self.inputs.l_45,'P_Factor'],'Sediment Delivery Ratio Strip Crop':[self.inputs.l_45,'Delivery_Ratio'],'Drain Rate':[self.inputs.l_46,'Drain_Rate'],'Invert Depth':[self.inputs.l_46,'Invert_Depth']}
        dic_climate = {'Station Latitude':[self.inputs.l_48,'Latitude'],'Station Longitude':[self.inputs.l_48,'Longitude'],'Station Elevation':[self.inputs.l_48,'Elevation'],'Adiabatic Air Temperature \nLapse Rate':[self.inputs.l_48,'Temperature_Lapse_Rate'],'Precipitation Nitrogen':[self.inputs.l_48,'Precipitation_N'],'Elevation Difference (1)':[self.inputs.l_48,'1st_Elevation_Difference'],'Elevation Rain Factor (1)':[self.inputs.l_48,'1st_Elevation_Rain_Factor'],'Elevation Difference (2)':[self.inputs.l_48,'2nd_Elevation_Difference'],'Elevation Rain Factor (2)':[self.inputs.l_48,'2nd_Elevation_Rain_Factor'],'2 Yr 24 Hr Precipitation':[self.inputs.l_48,'2_Yr_24_hr_Precipitation'],'Rainfall Calibration or Areal \nCorrection Coefficient':[self.inputs.l_48,'Calibration_or_Areal_Correction_Coefficient'],'Areal Rainfall \nCorrection Exponent':[self.inputs.l_48,'Calibration_or_Areal_Correction_Exponent'],'Minimum interception \nevaporation station':[self.inputs.l_48,'Minimum_Interception_Evaporation'],'Maximum interception \nevaporation station':[self.inputs.l_48,'Maximum_Interception_Evaporation'],'EI_Pct_01':[self.inputs.l_50,'EI_Pct_01'],'EI_Pct_02':[self.inputs.l_50,'EI_Pct_02'],'EI_Pct_03':[self.inputs.l_50,'EI_Pct_03'],'EI_Pct_04':[self.inputs.l_50,'EI_Pct_04'],'EI_Pct_05':[self.inputs.l_50,'EI_Pct_05'],'EI_Pct_06':[self.inputs.l_50,'EI_Pct_06'],'EI_Pct_07':[self.inputs.l_50,'EI_Pct_07'],'EI_Pct_08':[self.inputs.l_50,'EI_Pct_08'],'EI_Pct_09':[self.inputs.l_50,'EI_Pct_09'],'EI_Pct_10':[self.inputs.l_50,'EI_Pct_10'],'EI_Pct_11':[self.inputs.l_50,'EI_Pct_11'],'EI_Pct_12':[self.inputs.l_50,'EI_Pct_12'],'EI_Pct_13':[self.inputs.l_50,'EI_Pct_13'],'EI_Pct_14':[self.inputs.l_50,'EI_Pct_14'],'EI_Pct_15':[self.inputs.l_50,'EI_Pct_15'],'EI_Pct_16':[self.inputs.l_50,'EI_Pct_16'],'EI_Pct_17':[self.inputs.l_50,'EI_Pct_17'],'EI_Pct_18':[self.inputs.l_50,'EI_Pct_18'],'EI_Pct_19':[self.inputs.l_50,'EI_Pct_19'],'EI_Pct_20':[self.inputs.l_50,'EI_Pct_20'],'EI_Pct_21':[self.inputs.l_50,'EI_Pct_21'],'EI_Pct_22':[self.inputs.l_50,'EI_Pct_22'],'EI_Pct_23':[self.inputs.l_50,'EI_Pct_23'],'EI_Pct_24':[self.inputs.l_50,'EI_Pct_24']}
        dic_simulation = {'Headcut detachment leading coefficient (a)':[self.inputs.l_56,'Hdct_Detachment_Coef_a'],'Headcut detachment exponent coefficient (b)':[self.inputs.l_56,'Hdct_Detachment_Exp_Coef_b'],'Headcut erodibility leading coefficient (a)':[self.inputs.l_56,'Hdct_Erodibility_Coef_a'],'Headcut erodibility exponent coefficient (b)':[self.inputs.l_56,'Hdct_Erodibility_Exp_Coef_b'],'Minimum Interception Evaporation Global':[self.inputs.l_56,'Min_Interception_Evaporation'],'Maximum Interception Evaporation Global':[self.inputs.l_56,'Max_Interception_Evaporation'],'Detention Coefficient “a”':[self.inputs.l_56,'Detention_Coef_a'],'Detention Coefficient “b”':[self.inputs.l_56,'Detention_Coef_b'],'RCN Convergence Tolerance':[self.inputs.l_56,'RCN_Convergence_Tolerance'],'RCN Maximum Number of Iterations':[self.inputs.l_56,'RCN_Max_Iterations'],'Available Soil Moisture Ratio for AMC II':[self.inputs.l_56,'Avbl_Soil_Moist_Ratio_AMC_II'],'Maximum Available Sediment Concentration for Sheet Flow':[self.inputs.l_56,'Max_Avbl_Sed_Conc_for_Sht_Flw'],'Maximum Available Sediment Concentration for Concentrated Flow':[self.inputs.l_56,'Max_Avbl_Sed_Conc_for_Conc_Flw'],'Critical Shear Stress':[self.inputs.l_56,'Critical_Shear_Stress'],'Crop Initial Pesticide Amount 1':[self.inputs.l_57,'Crop_Initial_Amount_1'],'Crop Initial Pesticide Amount 2':[self.inputs.l_57,'Crop_Initial_Amount_2'],'Non-crop Initial Pesticide Amount 1':[self.inputs.l_57,'Non-Crop_Initial_Amount_1'],'Non-crop Initial Pesticide Amount 2':[self.inputs.l_57,'Non-Crop_Initial_Amount_2'],'Organic carbon from all sources':[self.inputs.l_58,'OC_All_Sources'],'Organic carbon from sheet & rill':[self.inputs.l_58,'OC_Sheet_and_Rill'],'Organic carbon from feedlot':[self.inputs.l_58,'OC_Feedlot'],'Organic carbon from point source':[self.inputs.l_58,'OC_Point_Source'],'Organic carbon from gully':[self.inputs.l_58,'OC_Gully'],'Organic carbon from pond':[self.inputs.l_58,'OC_Pond'],'Organic carbon from irrigation':[self.inputs.l_58,'OC_Irrigation'],'Nitrogen from all sources':[self.inputs.l_58,'N_All_Sources'],'Nitrogen from sheet & rill':[self.inputs.l_58,'N_Sheet_and_Rill'],'Nitrogen from feedlot':[self.inputs.l_58,'N_Feedlot'],'Nitrogen from point source':[self.inputs.l_58,'N_Point_Source'],'Nitrogen from gully':[self.inputs.l_58,'N_Gully'],'Nitrogen from pond':[self.inputs.l_58,'N_Pond'],'Nitrogen from irrigation':[self.inputs.l_58,'N_Irrigation'],'Phosphorus from all sources':[self.inputs.l_58,'P_All_Sources'],'Phosphorus from sheet & rill':[self.inputs.l_58,'P_Sheet_and_Rill'],'Phosphorus from feedlot':[self.inputs.l_58,'P_Feedlot'],'Phosphorus from point source':[self.inputs.l_58,'P_Point_Source'],'Phosphorus from gully':[self.inputs.l_58,'P_Gully'],'Phosphorus from pond':[self.inputs.l_58,'P_Pond'],'Phosphorus from irrigation':[self.inputs.l_58,'P_Irrigation'],'Sediment from all sources':[self.inputs.l_58,'Sediment_All_Sources'],'Sediment from sheet & rill':[self.inputs.l_58,'Sediment_Sheet_and_Rill'],'Sediment from feedlot':[self.inputs.l_58,'Sediment_Feedlot'],'Sediment from point source':[self.inputs.l_58,'Sediment_Point_Source'],'Sediment from gully':[self.inputs.l_58,'Sediment_Gully'],'Sediment from pond':[self.inputs.l_58,'Sediment_Pond'],'Sediment from irrigation':[self.inputs.l_58,'Sediment_Irrigation'],'Target Average Annual Direct Runoff Load':[self.inputs.l_59,'Target_AA_Direct_Runoff_Load'],'RCN Retention factor':[self.inputs.l_59,'RCN_Retention_Fctr'],'Reach Ratio':[self.inputs.l_59,'Reach_Ratio'],'Available Soil Moisture, AMC-II':[self.inputs.l_59,'Avbl_Soil_Moist_AMC_II'],'Rainfall factor':[self.inputs.l_60,'Rainfall_Fctr'],'10-yr EI':[self.inputs.l_60,'10-Year_EI'],'EI Number':[self.inputs.l_60,'EI_Number'],'Initialization Method Code':[self.inputs.l_60,'Init_Method_Code'],'Inorganic_N_1':[self.inputs.l_61,'Inorganic_N_1'],'Inorganic_N_2':[self.inputs.l_61,'Inorganic_N_2'],'Inorganic_P_1':[self.inputs.l_61,'Inorganic_P_1'],'Inorganic_P_2':[self.inputs.l_61,'Inorganic_P_2'],'Soil_Moisture_1':[self.inputs.l_61,'Soil_Moisture_1'],'Soil_Moisture_2':[self.inputs.l_61,'Soil_Moisture_2'],'Organic_Matter_1':[self.inputs.l_61,'Organic_Matter_1'],'Organic_Matter_2':[self.inputs.l_61,'Organic_Matter_2'],'Organic_N_1':[self.inputs.l_61,'Organic_N_1'],'Organic_N_2':[self.inputs.l_61,'Organic_N_2'],'Organic_P_1':[self.inputs.l_61,'Organic_P_1'],'Organic_P_2':[self.inputs.l_61,'Organic_P_2'],'Surface Residue':[self.inputs.l_61,'Surface_Residue'],'Manning’s n':[self.inputs.l_61,'Mannings_n'],'Snow Depth':[self.inputs.l_61,'Snow_Depth'],'Snow Density':[self.inputs.l_61,'Snow_Density'],'Surface Constant':[self.inputs.l_61,'Surface_Constant']}
        self.dic_name_column = {**dic_spatial,**dic_watershed, **dic_general, **dic_climate, **dic_simulation}
        
        #Change bounds in sensitivity dialog if distribution changed
        self.sensitivity_dialog.distributions.currentIndexChanged.connect(self.change_bounds)
        
        #Add new parameters to distribution in sensitivity dialog
        self.sensitivity_dialog.distributions.currentIndexChanged.connect(self.distribution_parameters)
        
        #Change number of samples in dialog depending on sensitivity analysis metod
        self.sensitivity_dialog.sobol.toggled.connect(self.change_sensitivity_metod)
        self.sensitivity_dialog.morris.toggled.connect(self.change_sensitivity_metod)
        self.sensitivity_dialog.trajectories.textChanged.connect(self.change_sensitivity_metod)
        
        #Add topagnps inputs with buttons
        self.dlg.pb_dem.clicked.connect(lambda _,b = "DEM":self.add_topagnps_input(b))
        self.dlg.pb_buffer.clicked.connect(lambda _,b = "buffer":self.add_topagnps_input(b))
        self.dlg.pb_vegetation.clicked.connect(lambda _,b = "vegetation":self.add_topagnps_input(b))
        self.dlg.pb_soil.clicked.connect(lambda _,b = "soil":self.add_topagnps_input(b))
        self.dlg.pb_management.clicked.connect(lambda _,b = "management":self.add_topagnps_input(b))
        
        #Add project folder if text was changed
        self.dlg.project.textChanged.connect(self.add_project_folder_text_changed)
        self.dlg.name_of_project.textChanged.connect(self.add_project_folder_text_changed)
        
        #Number of execution of sensitivity analysis
        self.numero_ejecucion = 1
        
        
        #Metod to open documentation
        lineEdits = [self.ctopagnps.info,self.cpeg.info,self.cagbuf.info,self.cagwet.info,self.cconcepts.info,self.cpothole.info,self.agflow.info,self.inputs.pushButton]
        for i in lineEdits:
            i.clicked.connect(lambda _,b = i:self.show_documentation(b))
        
        #Metod to delete control file
        lineEdits = [self.ctopagnps.delete_2,self.cpeg.delete_2,self.cagbuf.delete_2,self.cagwet.delete_2,self.cconcepts.delete_2,self.cpothole.delete_2,self.agflow.delete_2,self.agflow.delete_inp,self.dednm.delete_2,self.crasfor.delete_2,self.craspro.delete_2]
        for i in lineEdits:
            i.clicked.connect(lambda _,b = i:self.delete_control_file(b))
        
        #Coloreate buttons depending on existence of control files
        self.dlg.pbControl.clicked.connect(self.show_existing_control_files)
        
        #Open AnnAGNPS output folder
        self.output.open_folder.clicked.connect(self.open_annagnps_folder)
    
    def select_projects_without_output_scenario(self):
        """Method to select the projects without output in scenario analysis"""
        proyectos_seleccionados = [name for name, cb in self.checkboxes_project_scenario.items() if cb.isChecked()]
        
        proyectos_sin_output = []
        for proyecto in proyectos_seleccionados:
            if not os.path.exists(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_outputs\AnnAGNPS_TBL_Gaging_Station_Data_Hyd.csv"):
                proyectos_sin_output.append(proyecto)
        
        return proyectos_sin_output
    
    def execute_scenario_analysis(self):
        """Method to execute the project that don´t have the required output"""
        #First select the projects that don´t have the required output
        projects_without_output = self.select_projects_without_output_scenario()
        if len(projects_without_output) == 0:
            self.warning_message("All the projects have the required outputs, there is no need of execution")
            return
        
        #Do the execution
        #Function to modify or create the required file to display the required output
        def modify_input(proyecto,name_master,column,new_columns,name_new_file):
            master_file = self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs\\annagnps_master.csv"
            project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")

            if name_master in project_df.iloc[:,0].values:
                file = Path(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]==name_master].iloc[0,1])
                data = pd.read_csv(file,encoding = "ISO-8859-1",delimiter=",")
                # Eliminar espacios al inicio y final de los nombres de columnas
                data.columns = data.columns.str.strip()
                data[column].iloc[0] = "T"
                data.to_csv(file, index=False, float_format='%.5f')
                
            else:
                columns = new_columns
                data = pd.DataFrame(columns=columns, data=[[""] * len(columns)])
                data[column].iloc[0] = "T"
                nombre = name_new_file
                file = Path(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"\\simulation\\"+f"{nombre}.csv")
                data.to_csv(file, index=False, float_format='%.5f')
                project_df.loc[len(project_df)] = [name_master, f".\simulation\{nombre}.csv"]
                project_df.to_csv(master_file, index=False, float_format='%.5f')
        
        
        errors_projects = []
        for proyecto in projects_without_output:
            #Modify the master file
            columns = ["CCHE1D", "CONCEPTS_XML", "Gaging_Station_Hyd", "REMM", "Gaging_Station_Evt"]
            modify_input(proyecto,"Output Options - TBL","Gaging_Station_Hyd",columns,"out_tbl")
            
            #Execute
            #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
            self.time_start_processing = datetime.now()
            
            
            #EJECUCIÓN DE ANNAGNPS
            #os.chdir(self.direccion+"\\"+directory)
            def execute_bat():
               def main():
                   f = open(self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat","w+")
                   linea_uno = "CD /d {}".format(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs")
                   linea_dos = r"CALL {}\AnnAGNPS_v6.00.r.058_release_64-bit.exe".format(self.executable_directory)
                   f.write("{} \n".format(linea_uno))
                   f.write("{} \n".format(linea_dos))
                   f.close()
               main()
            execute_bat()

            subprocess.call(self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat")

            
            #If error file of AnnAGNPS is opened, then return a error message
            try:
                open(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"AnnAGNPS_LOG_Error.csv", "r+") 
            except PermissionError:
                self.warning_message("Error AnnAGNPS","Close AnnAGNPS_LOG_Error.csv before the start of execution")
                return
            except:
                pass
                        
            #PONER MENSAJE DE ERROR SI ANNAGNPS FUNCIONA MAL
            time.sleep(1)
            if path.exists(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"AnnAGNPS_LOG_Error.csv"):
                if os.stat(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"AnnAGNPS_LOG_Error.csv").st_size>0:
                    errors_projects.append(proyecto)
            
            #Los outputs de AnnAGNPS se guardan en Processing_outputs
            self.save_files_processing_in_folder_scenario(proyecto)
        
        
        
        if len(errors_projects)==0:
            self.warning_message("Executions completed")
        else:
            project_error_string = '","'.join(errors_projects)
            files_error = [self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_outputs\\AnnAGNPS_LOG_Error.csv" for proyecto in errors_projects]
            files_error_string = '","'.join(files_error)
            self.warning_message(f"The execution of the next projects gave error:{project_error_string}\nPlease check the next files to see the errors: {files_error_string}")

        #Update graph
        self.update_scenario_analysis_graph()
        
    def dlg_scenario_analysis_show(self):
        """Method to show the scenario analysis with all the projects"""
        lista = [
            f for f in os.listdir(self.carpeta_guardar_proyectos)
            if os.path.isdir(os.path.join(self.carpeta_guardar_proyectos, f))
        ]

        # Si ya tienes layout en Qt Designer
        layout = self.dlg_scenario_analysis.frame.layout()
        if layout is None:
            layout = QVBoxLayout(self.dlg_scenario_analysis.frame)
    
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.blockSignals(True)
                widget.deleteLater()

        # 1️Añadir el label arriba
        label = QLabel("Available projects")
        layout.addWidget(label)

        #Update available projects
        self.update_available_projects_scenario()
        
        #Update graph scenario analysis
        self.update_scenario_analysis_graph()
        
        # Mostrar el diálogo
        self.dlg_scenario_analysis.show()
        
    def update_available_projects_scenario(self):
        """Method to update the available projects in scenario analysis"""
        lista = [
            f for f in os.listdir(self.carpeta_guardar_proyectos)
            if os.path.isdir(os.path.join(self.carpeta_guardar_proyectos, f))
        ]
        
        layout = self.dlg_scenario_analysis.frame.layout()
        
        # 2️Crear los checkboxes
        self.checkboxes_project_scenario = {}

        for name in lista:
            checkbox = QCheckBox(name)
            layout.addWidget(checkbox)
            self.checkboxes_project_scenario[name] = checkbox
            setattr(self.dlg_scenario_analysis, name, checkbox)
            getattr(self.dlg_scenario_analysis, name).stateChanged.connect(lambda _: self.update_scenario_analysis_graph(False))

        # 3️Añadir un vertical spacer para empujar todo hacia arriba
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)
    
    
    def obtain_data_scenario_analysis(self,proyecto,date_changed):
        """Method to obtain data from the scenario analysis"""
        
        #First select the column of the information you want to see
        dictionary_columns = {self.dlg_scenario_analysis.total_discharge.text():"Total Streamflow",
            self.dlg_scenario_analysis.total_pesticide.text():"Pesticide: Total",
            self.dlg_scenario_analysis.total_carbon.text():"Organic Carbon: Total",
            self.dlg_scenario_analysis.total_phosphorus.text():"Phosphorus: Total",
            self.dlg_scenario_analysis.total_nitrogen.text():"Nitrogen: Total",
            self.dlg_scenario_analysis.total_sediment.text():"Sediment: All: Total"}
            
            
        selected_radio_button = next((w.text() for w in self.dlg_scenario_analysis.frame_2.findChildren(QRadioButton) if w.isChecked()), None)
        column = dictionary_columns[selected_radio_button]
        
        fichero = self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_outputs\AnnAGNPS_TBL_Gaging_Station_Data_Hyd.csv"
        if os.path.exists(fichero):
            first_column = "Gregorian Day"
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
               
            df_simulated = pd.DataFrame(columns = lista[0],data = lista[1:])
            df_simulated = df_simulated[df_simulated["Reach ID"]=="OUTLET"]
            df_simulated['date'] = pd.to_datetime(df_simulated[['Year', 'Month', 'Day']])
            # Encontrar la columna que contiene la información
            total_col = [col for col in df_simulated.columns if column in col][0]
            
            # Seleccionar solo la columna 'Date' y la columna de la información
            df_simulated = df_simulated[['date', total_col]]
            df_simulated[total_col] = df_simulated[total_col].astype(float)
            
            #Filter by date
            if date_changed:
                try:
                    fecha_inicio = pd.to_datetime(self.dlg_scenario_analysis.start_date.text())
                    fecha_fin = pd.to_datetime(self.dlg_scenario_analysis.end_date.text())
                    df_simulated = df_simulated[(df_simulated["date"] >= fecha_inicio) & (df_simulated["date"] <= fecha_fin)]
                except:
                    pass
            
            return df_simulated,total_col
        
        else:
            return 0,0
    
    def update_scenario_analysis_graph(self,date_changed=False): 
        """Method to udpate the graph of scenario analysis"""
        #Create the graph
        #Obtain data for all the checkboxes
        proyectos_seleccionados = [name for name, cb in self.checkboxes_project_scenario.items() if cb.isChecked()]
        
        dictionary_results = {}
        for proyecto in proyectos_seleccionados:
            df_simulated,total_col = self.obtain_data_scenario_analysis(proyecto,date_changed)
            if type(df_simulated) != int and type(total_col)!= int:
                #Save values
                dictionary_results[proyecto] = [df_simulated.date,df_simulated[total_col],df_simulated[total_col].sum()]
        
        #Add the graph
        if not hasattr(self, 'canvas_scenario'):
            #Create the canvas of the graph
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_scenario = FigureCanvas(plt.Figure(figsize=(15, 6)))
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_scenario_analysis.frame_3)
            self.dlg_scenario_analysis.frame_3.setLayout(layout)
            #Add canvas to layout
            layout.addWidget(self.canvas_scenario)
        
        #Add graph
        if len(dictionary_results)>0:
            self.canvas_scenario.figure.clear()
            self.ax_scenario_graph = self.canvas_scenario.figure.subplots()
            
            
            for i in dictionary_results.keys():
                self.ax_scenario_graph.plot(dictionary_results[i][0].to_numpy(),dictionary_results[i][1].to_numpy(),label = i,linewidth=2)
            
            
            self.ax_scenario_graph.legend()
            self.ax_scenario_graph.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
            self.ax_scenario_graph.set_ylabel(total_col,size = 12,family="arial",weight = "bold",color = "black")
            self.ax_scenario_graph.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            #Change background color
            self.canvas_scenario.figure.set_facecolor('#f0f0f0')
            self.ax_scenario_graph.set_facecolor('#f0f0f0')
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_scenario.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_scenario.figure.subplots_adjust(left=0.2, bottom=0.2)
            
            
            #Put the sums in the graph
            texto_sumas = ",".join([
                f"{proyecto}: {dictionary_results[proyecto][2]:.2f}"
                for proyecto in dictionary_results
            ])

            # Añadirlo debajo del gráfico
            self.canvas_scenario.figure.text(
                0.5, 0.01,
                texto_sumas,
                ha='center',
                va='bottom',
                fontsize=8,
                weight='bold',
                color='black'
            )
            
            
            #Draw canvas
            self.canvas_scenario.draw()
            
            #Put the dates in the text if another project was selected
            if not date_changed and len(dictionary_results)>0:
                xmin, xmax = self.ax_scenario_graph.get_xlim()
                self.dlg_scenario_analysis.start_date.setText(mdates.num2date(xmin).strftime("%Y-%m-%d"))
                self.dlg_scenario_analysis.end_date.setText(mdates.num2date(xmax).strftime("%Y-%m-%d"))
            
            
            
            self.canvas_scenario.figure.subplots_adjust(bottom=0.25)
            
            
            
            #Save figure
            self.dlg_scenario_analysis.print_graph.clicked.connect(lambda _, b= [self.dlg_scenario_analysis,self.canvas_scenario]:self.figure_settings(b))
            
       
    
    def save_figures(self): 
        """Method to save figures to the computer"""
        
        dialog =  self.information_figure_save[0]
        canvas =  self.information_figure_save[1]
        file_path, _ = QFileDialog.getSaveFileName(dialog, "Save graph", 
                                           os.path.join("C:\\", "graph.png"), 
                                            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;PDF Files (*.pdf);;All Files (*)")
        if file_path:
            #Change background color to white
            canvas.figure.set_facecolor('white')
            fig = canvas.figure
            axes = fig.get_axes()
            for axe in axes: 
                axe.set_facecolor('white')
            
            dpi_value = float(self.dlg_figure_settings.resolution.text())
            transparent = self.dlg_figure_settings.transparent.isChecked()
            tight = self.dlg_figure_settings.tight.isChecked()
            padding = float(self.dlg_figure_settings.padding.text())
            canvas.figure.savefig(file_path, dpi = dpi_value,bbox_inches='tight' if tight else None, 
                                         transparent=transparent, 
                                         pad_inches=padding)
        
            #Change background color again to original
            canvas.figure.set_facecolor('#f0f0f0')
            for axe in axes: 
                axe.set_facecolor('#f0f0f0')
            canvas.draw()
    
    
    
    def browse_files_sensitivity_results(self,information):
        """Method to select the file for sensitivity analysis graph between the local files for Morris and Sobol"""
        sensitivity_method, checkbox = information
        fname = QFileDialog.getOpenFileName(self.dlg_results_sensitivity, f"Select {sensitivity_method} Sensitivity Analysis Results File","C:\\" , "CSV files (*.csv)")
        if fname[0]!="":
            if sensitivity_method == "Morris":
                self.dlg_results_sensitivity.csv_results_morris.setText(fname[0])
            elif sensitivity_method == "Sobol":
                self.dlg_results_sensitivity.csv_results_2.setText(fname[0])

            #Set checked morris results
            checkbox.setChecked(True)
            #Update graph
            self.update_sensitivity_graph_global()
    
    def browse_inputs_calibration(self):
        """Method to browse inputs for calibration"""
        try:
            fname = QFileDialog.getOpenFileName(self.dlg_calibration_inputs, f"Select Inputs for calibration",self.direccion, "CSV files (*.csv)")
        except:
            fname = QFileDialog.getOpenFileName(self.dlg_calibration_inputs, f"Select Inputs for calibration","C:\\" , "CSV files (*.csv)")
        #Disconnect signal
        self.dlg_calibration_inputs.lineEdit.textChanged.disconnect(self.update_graph_calibration_inputs)
        if fname[0]!="":
            self.dlg_calibration_inputs.lineEdit.setText(fname[0])
            #Update graph
            self.update_graph_calibration_inputs()
        #Connect signal again
        self.dlg_calibration_inputs.lineEdit.textChanged.connect(self.update_graph_calibration_inputs)
    
    
    def browse_results_calibration(self):
        """Method to browse Results for calibration"""
        try:
            fname = QFileDialog.getOpenFileName(self.dlg_calibration_results, f"Select Results for calibration",self.direccion+"\\Calibration", "CSV files (*.csv)")
        except:
            fname = QFileDialog.getOpenFileName(self.dlg_calibration_results, f"Select Results for calibration","C:\\" , "CSV files (*.csv)")
        #Disconnect signal
        self.dlg_calibration_results.results.textChanged.disconnect(self.update_graph_calibration_results)
        if fname[0]!="":
            self.dlg_calibration_results.results.setText(fname[0])
            #Update graph
            self.update_graph_calibration_results()
        #Connect signal again
        self.dlg_calibration_results.results.textChanged.connect(self.update_graph_calibration_results)
    
    
    def update_graph_calibration_results(self):
        """Method to update results"""
        path = self.dlg_calibration_results.results.text()
        if os.path.exists(path) and os.path.isfile(path):    
            #First add the text
            with open(path, "r") as archivo:
                lineas = archivo.readlines()
            contenido = ""
            times = []
            observed = []
            simulated = []
            
            obtain_contenido = True
            
            for k,i in enumerate(lineas):
                if obtain_contenido:
                    contenido += i
                
                if "Nash-Sutcliffe efficiency" in i:
                    obtain_contenido = False
                    
                if i[:5]=="date,":
                    for m in range(k+1,len(lineas)):
                        if "Results of each iteration" in lineas[m]:
                            break
                        try:
                            times.append(pd.to_datetime(lineas[m].split(",")[0], errors='coerce'))
                        except:
                            times.append(0)
                        try:
                            observed.append(float(lineas[m].split(",")[1]))
                        except:
                            observed.append(0)
                        try:
                            simulated.append(float(lineas[m].split(",")[2]))
                        except:
                            simulated.append(0)
                        
            self.dlg_calibration_results.textEdit.setPlainText(contenido)
            #Add the graph
            if not hasattr(self, 'canvas_calibration_graph'):
                #Create the canvas of the graph
                # Si no existe, crear el canvas y añadirlo al layout
                self.canvas_calibration_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
                # Asignar un layout al QFrame si no tiene uno
                layout = QVBoxLayout(self.dlg_calibration_results.frame)
                self.dlg_calibration_results.frame.setLayout(layout)
                #Add canvas to layout
                layout.addWidget(self.canvas_calibration_graph)
            
            #Add graph
            self.canvas_calibration_graph.figure.clear()
            self.ax_calibration_graph = self.canvas_calibration_graph.figure.subplots()
            
            if self.dlg_calibration_results.one_one.isChecked():
                self.ax_calibration_graph.scatter(simulated, observed,color = "blue")
                #1:1 line
                max_val = max(simulated + observed)
                self.ax_calibration_graph.plot([0, max_val], [0, max_val], linestyle='--', color='black')
                self.ax_calibration_graph.set_xlabel("Simulated",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph.set_ylabel("Observed",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph.tick_params(axis = "both",colors = "black",labelsize = 9)

                
            elif self.dlg_calibration_results.graph_fit.isChecked():
                self.ax_calibration_graph.plot(times,simulated,label = "Simulated",linewidth=2,zorder = 1)
                self.ax_calibration_graph.scatter(times,observed,label = "Observed",color = "orange",zorder = 2)
                
                
                self.ax_calibration_graph.legend()
                self.ax_calibration_graph.set_xlabel("Time (s)",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph.set_ylabel("Total streamflow",size = 12,family="arial",weight = "bold",color = "black")
                self.ax_calibration_graph.tick_params(axis = "both",colors = "black",labelsize = 9)
            
            #Change background color
            self.canvas_calibration_graph.figure.set_facecolor('#f0f0f0')
            self.ax_calibration_graph.set_facecolor('#f0f0f0')
            
            # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
            self.canvas_calibration_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
            self.canvas_calibration_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
            #Draw canvas
            self.canvas_calibration_graph.draw()
            
            #Save figure
            self.dlg_calibration_results.print_graph.clicked.connect(lambda _, b= [self.dlg_calibration_results,self.canvas_calibration_graph]:self.figure_settings(b))
            
    
    
    def update_graph_calibration_inputs(self):
        """Method to update the graph of the inputs of calibration"""
        #Create and clear axis before drawing
        if not hasattr(self, 'canvas_calibration_graph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_calibration_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_calibration_inputs.frame)
            self.dlg_calibration_inputs.frame.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_calibration_graph)
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_calibration_graph.figure.clear()
            
        try:
                
            self.ax_calibration_inputs = self.canvas_calibration_graph.figure.subplots()
            self.canvas_calibration_graph.figure.set_facecolor('#87CEEB') # Fondo exterior
            self.ax_calibration_inputs.set_facecolor('#87CEEB')
            
            file_path = self.dlg_calibration_inputs.lineEdit.text()
            df = pd.read_csv(file_path, sep=',', header=None)
            if len(df.columns)!=2:
                self.warning_message("The selected file has not two columns of data. \nThe data must contain two columns, the first one for the date and the second one for the values")
                return
            df.columns = ['date', 'value']

            # 2. Conversión y Limpieza
            df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna().sort_values('date')

            # 3. Configuración del Gráfico
            # IMPORTANTE: Usamos .values para evitar el ValueError
            line_color = '#2C3E50'
            self.ax_calibration_inputs.plot(
                df['date'].values, 
                df['value'].values, 
                color=line_color, 
                marker='o', 
                markersize=4, 
                linewidth=1.5, 
                label='Data'
            )

            # 4. Personalización de Ejes (Sin título)
            self.ax_calibration_inputs.set_ylabel('Observed value', fontsize=12, color='#333333')
            self.ax_calibration_inputs.set_xlabel('Time', fontsize=12, color='#333333')

            # --- ESTILO "AXIS" (MARCO CERRADO) ---
            for spine in self.ax_calibration_inputs.spines.values():
                spine.set_visible(True)
                spine.set_color('#333333')
                spine.set_linewidth(1)

            # Separador de miles
            self.ax_calibration_inputs.yaxis.set_major_formatter(
                ticker.FuncFormatter(lambda x, p: format(int(x), ','))
            )

            # --- CONFIGURACIÓN DEL EJE X ---
            self.ax_calibration_inputs.xaxis.set_major_locator(mdates.YearLocator())
            self.ax_calibration_inputs.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            self.ax_calibration_inputs.xaxis.set_minor_locator(mdates.MonthLocator())

            # Estética de Ticks (direction='in' para estilo técnico)
            self.ax_calibration_inputs.tick_params(axis='x', which='major', length=10, width=1.2, labelsize=11, bottom=True, top=True, direction='in')
            self.ax_calibration_inputs.tick_params(axis='x', which='minor', length=5, width=0.8, bottom=True, top=True, direction='in')
            self.ax_calibration_inputs.tick_params(axis='y', which='major', length=6, left=True, right=True, direction='in')

            # Rejilla muy sutil
            self.ax_calibration_inputs.grid(axis='y', linestyle='--', alpha=0.15)

            # Ajustar márgenes y dibujar
            self.canvas_calibration_graph.figure.subplots_adjust(left=0.15, bottom=0.2, right=0.95, top=0.9)
            self.canvas_calibration_graph.draw()
            
        except:
            #If output doesnt exist, then stop with the code
            self.canvas_calibration_graph.figure.clear()
            #If I clear but not .draw() then is changed but only when dialog is maximized or minimized
            self.canvas_calibration_graph.draw()
            return
    
    
    def open_annagnps_folder(self):
        #Metod to open AnnAGNPS output folder
        try:
            os.startfile(self.output.lineEdit.text())
        except:
            pass
        
    def show_existing_control_files(self):
        #Metod to show existing control files
        try:
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\TOPAGNPS.csv"):
                self.cgeneral.pushButton.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton.setStyleSheet("background-color: #becbd1;")
                
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\PEG.csv"):
                self.cgeneral.pushButton_2.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_2.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AGBUF.csv"):
                self.cgeneral.pushButton_3.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_3.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AGWET.csv"):
                self.cgeneral.pushButton_4.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_4.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\CONCEPTS.csv"):
                self.cgeneral.pushButton_5.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_5.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\POTHOLE.csv"):
                self.cgeneral.pushButton_6.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_6.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AGFLOW.csv") or os.path.exists(self.direccion+"\AGFCNT.inp"):
                self.cgeneral.pushButton_9.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_9.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\dednm.inp"):
                self.cgeneral.pushButton_10.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_10.setStyleSheet("background-color: #becbd1;")
            
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\rasfor.inp"):
                self.cgeneral.pushButton_8.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_8.setStyleSheet("background-color: #becbd1;")
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\raspro.inp"):
                self.cgeneral.pushButton_7.setStyleSheet("background-color: #66FF66; color: black;")
            else:
                self.cgeneral.pushButton_7.setStyleSheet("background-color: #becbd1;")
            
        except:
            pass
    
    def delete_control_file(self,doc):
        #Metod to delete control file
        try:
            if doc==self.ctopagnps.delete_2:
                self.ctopagnps.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\TOPAGNPS.csv")
            if doc==self.cpeg.delete_2:
                self.cpeg.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\PEG.csv")
            if doc==self.cagbuf.delete_2:
                self.cagbuf.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\AGBUF.csv")
            if doc==self.cagwet.delete_2:
                self.cagwet.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\AGWET.csv")
            if doc==self.cconcepts.delete_2:
                self.cconcepts.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\CONCEPTS.csv")
            if doc==self.cpothole.delete_2:
                self.cpothole.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\POTHOLE.csv")
            if doc==self.agflow.delete_2:
                self.agflow.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\AGFLOW.csv")
            if doc==self.agflow.delete_inp:
                self.agflow.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\AGFCNT.inp")
            if doc==self.dednm.delete_2:
                self.dednm.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"\dednm.inp")
            if doc==self.crasfor.delete_2:
                self.crasfor.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"/rasfor.inp")
            if doc==self.craspro.delete_2:
                self.craspro.close()
                os.remove(self.direccion+"\\Preprocessing_inputs"+"/raspro.inp")
        except:
            pass
        
        #Update use of control files
        self.show_existing_control_files()
        
    def show_documentation(self,doc):
        #Metod to show documentation file
        try:
            if doc==self.ctopagnps.info:
                os.startfile(self.plugin_directory+"\Documentation\TopAGNPS_User_Manual.pdf")
            if doc==self.cpeg.info:
                os.startfile(self.plugin_directory+"\Documentation\PEG_User_Manual.pdf")
            if doc==self.cagbuf.info:
                os.startfile(self.plugin_directory+"\Documentation\AGBUF_User_Manual.pdf")
            if doc==self.cagwet.info:
                os.startfile(self.plugin_directory+"\Documentation\AGWET_User_Manual.pdf")
            if doc==self.cconcepts.info:
                os.startfile(self.plugin_directory+"\Documentation\CONCEPTS_User_Manual.pdf")
            if doc==self.cpothole.info:
                os.startfile(self.plugin_directory+"\Documentation\POTHOLE_User_Manual.pdf")
            if doc==self.agflow.info:
                os.startfile(self.plugin_directory+"\Documentation\AGFLOW_User_Manual.pdf")
            if doc==self.inputs.pushButton:
                os.startfile(self.plugin_directory+"\Documentation\Input_Specifications.pdf")
        except:
            pass
       
    def instantiate_buffer(self):
        #Metod to select the layer of buffer that is going to be used
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        selectedLayerIndex = self.dlg.comboBox_2.currentIndex()-1
        if selectedLayerIndex>=0:
            selectedLayer = layers[selectedLayerIndex].layer()
            self.fichero_buf =  selectedLayer.dataProvider().dataSourceUri()
            buf_directory, self.nombre_buf = os.path.split(self.fichero_buf)
            #Create file if it doesn't exist
            if not os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV"):
                control_file = pd.DataFrame(data = {"BUFFER":[self.nombre_buf],"VEGETATION":"",
                                    "FOREST":"","GRASS":"",
                                    "C_THRESHOLD":"","R_THRESHOLD":"",
                                    "UNITS":"","ASC_PATH":"",
                                    "CSV_PATH":""})
                control_file.to_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"AGBUF.csv", index=False, float_format='%.5f')
            
        #Add name of Buffer to AGBUF.csv if this file exists
        try: #when opening the plugin self.direccion doesnt exist
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV"):
                if selectedLayerIndex==-1:self.nombre_buf=""
                topagnps_control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV",encoding = "ISO-8859-1",delimiter=",")
                topagnps_control_file["BUFFER"].iloc[0]=self.nombre_buf
                topagnps_control_file.to_csv(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV", index=False, float_format='%.5f')
        except:
            pass
        
        
    def instantiate_vegetation(self):
        #Metod to select the layer of vegetation that is going to be used
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        selectedLayerIndex = self.dlg.comboBox_3.currentIndex()-1
        if selectedLayerIndex>=0:
            selectedLayer = layers[selectedLayerIndex].layer()
            self.fichero_veg =  selectedLayer.dataProvider().dataSourceUri()
            veg_directory, self.nombre_veg = os.path.split(self.fichero_veg)
            #Create file if it doesn't exist
            if not os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV"):
                control_file = pd.DataFrame(data = {"BUFFER":"","VEGETATION":[self.nombre_veg],
                                    "FOREST":"","GRASS":"",
                                    "C_THRESHOLD":"","R_THRESHOLD":"",
                                    "UNITS":"","ASC_PATH":"",
                                    "CSV_PATH":""})
                control_file.to_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"AGBUF.csv", index=False, float_format='%.5f')
                
        #Add name of Buffer to AGBUF.csv if this file exists
        try: #when opening the plugin self.direccion doesnt exist
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV"):
                if selectedLayerIndex==-1:self.nombre_veg=""
                topagnps_control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV",encoding = "ISO-8859-1",delimiter=",")
                topagnps_control_file["VEGETATION"].iloc[0]=self.nombre_veg
                topagnps_control_file.to_csv(self.direccion+"\\Preprocessing_inputs"+"\\AGBUF.CSV", index=False, float_format='%.5f')
        except:
            pass
            
                
    def instantiate_soil(self):
        #Metod to select the layer of soil that is going to be used
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        selectedLayerIndex = self.dlg.cbSoil.currentIndex()-1
        
        if selectedLayerIndex>=0:
            selectedLayer = layers[selectedLayerIndex].layer()
            self.fichero_soil =  selectedLayer.dataProvider().dataSourceUri()
            try:
                self.epsg_soil = selectedLayer.crs().authid().split(":")[1]
            except:
                self.epsg_soil = "No defined"
        
    def instantiate_management(self):
        #Metod to select the layer of management that is going to be used
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        selectedLayerIndex = self.dlg.cbMan.currentIndex()-1
        if selectedLayerIndex>=0:
            selectedLayer = layers[selectedLayerIndex].layer()
            self.fichero_manag =  selectedLayer.dataProvider().dataSourceUri()
            try:
                self.epsg_manag = selectedLayer.crs().authid().split(":")[1]
            except:
                self.epsg_manag = "No defined"
    
    
    def add_project_folder_text_changed(self):
        #Metod to add project folder if text was changed
        self.direccion = str(self.dlg.project.text())+"\\"+self.dlg.name_of_project.text()
        #Asignar los valores de los control files a los diálogos
        self.asignar_valores_control_dialogo()
        #Poner el nombre de la carpeta en los outputs
        self.output.lineEdit.setText(self.direccion+r"\INPUTS")
        self.output.lineEdit_2.setText(self.direccion)
        #Update existing control files
        self.show_existing_control_files()
    
    def add_topagnps_input(self,type_input):
        #Metod to add topagnps inputs with pushbutton
        if hasattr(self,"direccion"):
            fname = QFileDialog.getOpenFileName(self.inputs,f"Select {type_input} file",self.direccion)
        else:
            fname = QFileDialog.getOpenFileName(self.inputs,f"Select {type_input} file","C/")
        if fname[0]!="":
            dic = {"DEM":self.dlg.comboBox,"buffer":self.dlg.comboBox_2,"vegetation":self.dlg.comboBox_3,"soil":self.dlg.cbSoil,"management":self.dlg.cbMan}
            combo = dic[type_input]
            #Se añade el archivo al canvas
            if type_input=="DEM" or type_input=="buffer" or type_input=="vegetation":
                layer = QgsRasterLayer(fname[0],type_input)
                if not layer.isValid():
                    iface.messageBar().pushMessage("Please select a raster file",level=Qgis.Warning)
                    return
            else:
                layer = QgsVectorLayer(fname[0],type_input)
                if not layer.isValid():
                    iface.messageBar().pushMessage("Please select a vector file",level=Qgis.Warning)
                    return
                    
            QgsProject.instance().addMapLayer(layer, False)
            root = QgsProject.instance().layerTreeRoot()
            root.insertLayer(0, layer)
            #QgsProject.instance().addMapLayer(layer)
            
            
            #Se obtienen las capas que hay en el canvas
            all_layers = QgsProject.instance().layerTreeRoot().children()
            layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
            project_layers=[layer.name() for layer in layers]
            project_layers.insert(0,"")
            
            
            #Se actualizan las capas
            
            #Si se actualiza la capa de suelo, no se quiere que se cambien las columnas de manejo, y viceversa. 
            if type_input == "soil":
                self.dlg.cbMan.currentIndexChanged.disconnect(self.cambios_manejo)
            
            elif type_input == "management":
                self.dlg.cbSoil.currentIndexChanged.disconnect(self.cambios_suelo)
            
            
            for i in dic.keys():
                if i!=type_input:
                    index = dic[i].currentIndex()
                    if index ==0:index =-1
                else:index = 0
                #Clear
                dic[i].clear()
                #Add values
                dic[i].addItems(project_layers)
                #Se ponen bien los índices
                dic[i].setCurrentIndex(index+1)              
            
            #Se vuelven a conectar
            if type_input == "soil":
                self.dlg.cbMan.currentIndexChanged.connect(self.cambios_manejo)
            
            elif type_input == "management":
                self.dlg.cbSoil.currentIndexChanged.connect(self.cambios_suelo)
        
        
    def add_project_folder(self):
        #Metod to add the folder of project to line
        fname = QFileDialog.getExistingDirectory(self.dlg, "Select folder", "C/")
        #Condiciones en donde si se elige un archivo y la carpeta coincide con la de su sección, solo se pone el nombre del archivo, sino toda la dirección.
        if fname!="":
            self.dlg.project.setText(fname)
        #Make project directory
        self.direccion = str(self.dlg.project.text())+"\\"+self.dlg.name_of_project.text()
        #Poner el nombre de la carpeta en los outputs
        self.output.lineEdit.setText(self.direccion+r"\INPUTS")
        self.output.lineEdit_2.setText(self.direccion)
        #Pone la dirección del proyecto en las direcciones de las carpetas de los inputs de annagnps
        self.files_directory()
        #Put the epsg of the project
        self.epsg = QgsProject.instance().crs().authid()
        
    def obtener_codificacion(self,archivo_csv):
        #Metod to detect code type of csv. If I dont do this ' character gives an error for example in Global IDs, Factors and Flags. 
        with open(archivo_csv, 'rb') as file:
            resultado = chardet.detect(file.read())
        return resultado['encoding']
    
    def instantiate_table(self):
        #Metod to instantiate the dialog for the inputs of annagnps in a table
        #Counter of number of table inputs. If they are removed we dont substract value. Its just to have diferente attributes names.
        if hasattr(self,"cantidad_table_inputs"):
            self.cantidad_table_inputs+=1
        else:
            self.cantidad_table_inputs = 0
        
        #Create class
        FORM_CLASS, _ = uic.loadUiType(os.path.join(self.plugin_directory, "ui/table_inputs.ui"))
        class TableDialog(QtWidgets.QDialog, FORM_CLASS):
            def __init__(self, parent=None):
                super(TableDialog, self).__init__(parent)
                self.setupUi(self)
        
        return TableDialog()
    
    def table_inputs_front(self):
        #To put AnnANGPS table inputs to the front
        clases_table_inputs = [getattr(self, x) for x in self.__dict__.keys() if x[:12]=="table_input_" and x[12]!="o"]
        for i in clases_table_inputs:
            i.raise_()
    
    def table_inputs(self,button):
        #Metod to add a dialog where inputs of AnnAGNPS can be modified
        #First we instantiate the dialog. If we do the classic way we could only choose one dialog and we want the possibility of obtaining many.
        table_class = self.instantiate_table()
        setattr(self,f"table_input_{self.cantidad_table_inputs}",table_class)
        self.button = button #for when we are in overwriting
        #Icons
        table_class.add.setIcon(QIcon(os.path.join(self.plugin_directory, "images/add.svg")))
        table_class.remove.setIcon(QIcon(os.path.join(self.plugin_directory, "images/remove.svg")))
        
        #Function to return the path depending if the file path is absolute or relative
        def file_input(boton):
            if os.path.isabs(self.dic_line_table[button].text()):
                return self.dic_line_table[button].text()
            else:
                return self.dic_folder[self.dic_line_table[button]].text()+"/"+self.dic_line_table[button].text() 
        
        #Condition adding data to table when there is not a csv written. 
        if self.dic_line_table[button].text() =="":
            #If file exist then warning
            name_file = self.dic_table_filename[button]
            file_path = self.dic_folder[self.dic_line_table[button]].text()+"/"+name_file
            if path.exists(file_path) and self.table_input_overwrite == False and os.path.getsize(file_path)>0:
                self.overwrite.show()
                self.overwrite.label.setText(f"{file_path} exist. Do you want to overwrite the file?")
                self.overwriting_input = True #to say to the button "Yes" that we are modifying with table and not with CSV file
                return
            #Add files and columns
            #Add columns
            columnas = self.dic_table_button[button]
            table_class.tableWidget.setColumnCount(len(columnas))
            table_class.tableWidget.setHorizontalHeaderLabels(columnas)
            table_class.tableWidget.resizeColumnsToContents()
            #Add name to dialog
            table_class.setWindowTitle(" ".join([x.capitalize() for x in name_file.split("_")]))
            #Show dialog
            table_class.show()
            #This is to put the annagnps inputs in the front
            self.table_inputs_front()
            
        #Condition if we have csv written, exists and its size is 0
        elif os.path.exists(file_input(button)) and os.path.getsize(file_input(button))==0:
            name_file = self.dic_table_filename[button]
            #Add files and columns
            #Add columns
            columnas = self.dic_table_button[button]
            table_class.tableWidget.setColumnCount(len(columnas))
            table_class.tableWidget.setHorizontalHeaderLabels(columnas)
            table_class.tableWidget.resizeColumnsToContents()
            #Add name to dialog
            table_class.setWindowTitle(" ".join([x.capitalize() for x in name_file.split("_")]))
            #Show dialog
            table_class.show()
            #This is to put the annagnps inputs in the front
            self.table_inputs_front()
            
        else:
            file_path = file_input(button)
            if self.dic_line_table[button].text() == "-- Provided by TopAGNPS --":
                file_path = self.direccion+"\\Preprocessing_outputs"+"\\"+ os.path.basename(self.file_input(self.dic_line_table[button]))
            if os.path.exists(file_path) and os.path.getsize(file_path)>0: 
                #Add files and columns
                #Add columns
                def obtener_datos_filas(archivo_csv):
                    datos_filas = []
                    # Determinar la codificación del archivo CSV
                    codificacion = self.obtener_codificacion(archivo_csv)
                    with open(archivo_csv, 'r', encoding=codificacion) as file:
                        reader = csv.reader(file)
                        # Leer la primera fila del archivo CSV (nombres de las columnas)
                        nombres_columnas = next(reader)
                        # Iterar sobre las filas restantes y construir la lista de listas
                        for fila in reader:
                            datos_filas.append(fila)
                    return nombres_columnas, datos_filas
                    
                columnas, datos_filas = obtener_datos_filas(file_path)
                table_class.tableWidget.setColumnCount(len(columnas))
                table_class.tableWidget.setHorizontalHeaderLabels(columnas)
                table_class.tableWidget.resizeColumnsToContents()
                #Add rows
                table_class.tableWidget.setRowCount(len(datos_filas))
                for fila, datos in enumerate(datos_filas):
                    for columna, valor in enumerate(datos):
                        item = QTableWidgetItem(valor)
                        table_class.tableWidget.setItem(fila, columna, item)
                        item.setTextAlignment(Qt.AlignCenter)
                #Add name to dialog
                table_class.setWindowTitle(" ".join([x.capitalize() for x in self.dic_table_filename[button].split("_")]))
                #Show dialog
                table_class.show()
                #This is to put the annagnps inputs in the front
                self.table_inputs_front()
                    
            elif not os.path.exists(file_path) and self.dic_line_table[button].text() != "-- Provided by TopAGNPS --":
                self.existing.label.setText("{} does not exist".format(file_path))
                self.existing.show()
        
        #Add the functionality to the dialog to add and remove rows and create document
        table_class.add.clicked.connect(lambda _,b = self.cantidad_table_inputs:self.add_row(b))
        table_class.remove.clicked.connect(lambda _,b = self.cantidad_table_inputs:self.remove_row(b))
        table_class.accept.clicked.connect(lambda _,b = button, c=self.cantidad_table_inputs:self.create_file_table(b,c))
        table_class.rejected.connect(self.table_inputs_front) #when dialog is closed put the rest of annagnps table inputs to the front
    
    
    def create_file_table(self,button,numero_table_input):
        #Metod to create or upload file when modifying AnnAGNPS input with the table
        #First we instantiate the variable of the dialog
        table_input = getattr(self, f"table_input_{numero_table_input}")
        #Then we determine the file path
        if self.dic_line_table[button].text()=="-- Provided by TopAGNPS --":
            file_path = self.direccion+"\\Preprocessing_outputs"+"\\"+os.path.basename(self.file_input(self.dic_line_table[button]))    
        elif os.path.isabs(self.dic_line_table[button].text()):
            file_path =  self.dic_line_table[button].text()
        else:
            file_path =  self.dic_folder[self.dic_line_table[button]].text()+"/"+self.dic_line_table[button].text() 
        #Now we create or upload the files
        if self.dic_line_table[button].text() == "":
            #Here we create a new file
            name_file = self.dic_table_filename[button]
            file_path = self.dic_folder[self.dic_line_table[button]].text()+"/"+name_file
            with open(file_path, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                # Get column names from the table
                column_names = [table_input.tableWidget.horizontalHeaderItem(col).text() for col in range(table_input.tableWidget.columnCount())]
                csv_writer.writerow(column_names)
                # Get row data from the table
                for row in range(table_input.tableWidget.rowCount()):
                    row_data = []
                    for col in range(table_input.tableWidget.columnCount()):
                        try: #this is because if there is not data in the cell then it gives error
                            row_data.append(table_input.tableWidget.item(row, col).text())
                        except:
                            row_data.append("")
                    csv_writer.writerow(row_data)
            self.dic_line_table[button].setText(name_file)
            table_input.close()
            self.table_inputs_front()
        else:
            #Here we upload the file
            try:
                codificacion = self.obtener_codificacion(file_path)
                with open(file_path, 'w', newline='',encoding=codificacion) as csv_file:
                    csv_writer = csv.writer(csv_file)
                    # Get column names from the table
                    column_names = [table_input.tableWidget.horizontalHeaderItem(col).text() for col in range(table_input.tableWidget.columnCount())]
                    csv_writer.writerow(column_names)
                    # Get row data from the table
                    for row in range(table_input.tableWidget.rowCount()):
                        row_data = []
                        for col in range(table_input.tableWidget.columnCount()):
                            try: #this is because if there is not data in the cell then it gives error
                                row_data.append(table_input.tableWidget.item(row, col).text())
                            except:
                                row_data.append("")
                        csv_writer.writerow(row_data)
                table_input.close()
                self.table_inputs_front()
            except:
                iface.messageBar().pushMessage(f"Please close {file_path} to update data",level=Qgis.Warning,duration = 10)
                return
    
    def add_row(self,numero_table_input):
        #Metod to add rows in tables for AnnAGNPS inputs
        table_input = getattr(self, f"table_input_{numero_table_input}")
        row_position = table_input.tableWidget.rowCount()
        table_input.tableWidget.insertRow(row_position)

    def remove_row(self,numero_table_input):
        #Metod to remove rows in tables for AnnAGNPS inputs
        table_input = getattr(self, f"table_input_{numero_table_input}")
        selected_row = table_input.tableWidget.rowCount()
        if selected_row >= 0:
            table_input.tableWidget.removeRow(selected_row-1)
        
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
            self.output.lineEdit_6.setText(f"{round(float(self.average_total),2)} {self.units}")
            self.output.lineEdit_7.setText(f"{round(float(self.average_anual),2)} {self.units}")
            self.output.lineEdit_8.setText(f"{round(float(self.highest_anual[1]),2)} {self.units}")
            self.output.lineEdit_10.setText(f"{int(self.highest_anual[0])}")
            self.output.lineEdit_9.setText(f"{round(float(self.lowest_anual[1]),2)} {self.units}")
            self.output.lineEdit_11.setText(f"{int(self.lowest_anual[0])}")
        else:
            self.output.lineEdit_6.setText(f"{round(float(self.average_total),2)} {self.units}")
            self.output.lineEdit_7.setText(f"{round(float(self.average_anual),2)} {self.units}")
            self.output.lineEdit_8.setText(f"{round(float(self.highest_anual[1]),2)} {self.units}")
            self.output.lineEdit_10.setText(f"{int(self.highest_anual[0])}")
            self.output.lineEdit_9.setText(f"{round(float(self.lowest_anual[1]),2)} {self.units}")
            self.output.lineEdit_11.setText(f"{int(self.lowest_anual[0])}")
    
    def spatial_output(self):
        #Método para poner los outputs espaciales
        #Si no se ha elegido la carpeta correcta entonces que pare el código
        if not self.file_exist:
            return
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
            iface.messageBar().pushMessage(f"AnnAGNPS_Cell_IDs.asc not found: AnnAGNPS_Cell_IDs.asc file must be in {os.path.dirname(self.output.lineEdit.text())}",level=Qgis.Warning)
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
            iface.messageBar().pushMessage("Some error with CRS has ocurred: Please select another CRS for the project",level=Qgis.Warning)
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
            iface.messageBar().pushMessage("Please select correct dates",level=Qgis.Warning)
            self.error = True
            return
        #Se obtienen los datos ordenados
        if self.data_type == "Runoff":
            path = self.output.lineEdit.text()+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            try:
                df_raw = self.df_section_output(path,delete_second=True).iloc[2:,]
            except:
                iface.messageBar().pushMessage(f"{path} has not a correct format",level=Qgis.Warning)
                self.error = True
                return
            df = pd.DataFrame(data = {"Year": df_raw["Year"].astype(int),"Month": df_raw["Month"].astype(int),"Day": df_raw["Day"].astype(int),"Cell": df_raw["ID"].astype(int),"Runoff": df_raw["Depth"].astype(float),"RSS": df_raw["Rainfall"].astype(float) + df_raw["Snowfall"].astype(float) + df_raw["Snowmelt"].astype(float) + df_raw["Irrigation"].astype(float)})
        else:
            dic_outputs = {"Subtotal":["AnnAGNPS_EV_Sediment_yield_(mass).csv"],"Gully":["AnnAGNPS_EV_Sediment_yield_(mass).csv"],"Pond":["AnnAGNPS_EV_Sediment_yield_(mass).csv"],"Sheet & Rill":["AnnAGNPS_EV_Sediment_yield_(mass).csv"],"Nitrogen":["AnnAGNPS_EV_Nitrogen_yield_(mass).csv"],"Carbon":["AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv"],"Phosphorus":["AnnAGNPS_EV_Phosphorus_yield_(mass).csv"]}
            path = self.output.lineEdit.text()+f"\\{dic_outputs[self.data_type][0]}"
            try:
                df_raw = self.df_section_output(path,delete_second=False)
            except:
                iface.messageBar().pushMessage(f"{path} has not a correct format",level=Qgis.Warning)
                self.error = True
                return
            self.units = df_raw.columns[-1][-4:]
            dic_outputs = {"Subtotal":["AnnAGNPS_EV_Sediment_yield_(mass).csv",f"Subtotals {self.units}"],"Gully":["AnnAGNPS_EV_Sediment_yield_(mass).csv",f"Subtotals {self.units}"],"Pond":["AnnAGNPS_EV_Sediment_yield_(mass).csv",f"Subtotals {self.units}"],"Sheet & Rill":["AnnAGNPS_EV_Sediment_yield_(mass).csv",f"Subtotals {self.units}"],"Nitrogen":["AnnAGNPS_EV_Nitrogen_yield_(mass).csv",f"Subtotal N {self.units}"],"Carbon":["AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv",f"Subtotal C {self.units}"],"Phosphorus":["AnnAGNPS_EV_Phosphorus_yield_(mass).csv",f"Subtotal P {self.units}"]}
            
                
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

    def import_df(self,data_type,core,sensitivity=False):
        #Método para importar el df que se usará en los outputs
        #Dar error si no se han escogido las fechas bien. Solo cuando no se esté haciendo el analisis de sensibilidad
        if not sensitivity:
            date_in = self.output.lineEdit_4.text()
            date_fin = self.output.lineEdit_5.text()
            try:
                date_in = datetime(int(date_in.split("/")[2]),int(date_in.split("/")[1]),int(date_in.split("/")[0]))
                date_fin = datetime(int(date_fin.split("/")[2]),int(date_fin.split("/")[1]),int(date_fin.split("/")[0]))
            except:
                self.warning_message("Please select correct dates")
                self.error = True
                return 
        #Primero si se ha elegido Runoff
        if data_type == "Runoff":
            #Se obtienen los datos ordenados
            path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            
            if not os.path.exists(path):
                self.warning_message("AnnAGNPS_SIM_Insitu_Soil_Moisture output not found. \nInsitu_Soil_Moisture_Daily column in OUTPUT OPTIONS DATA -SIM file must be set to T ")
                return
            
            if sensitivity: #cuando se hace el análisis de sensibilidad la ruta es otra
                path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            try:
                df_raw = self.df_section_output(path,delete_second=True).iloc[2:,]
            except:
                self.warning_message(f"{path} has not a correct format")
                self.error = True
                return
            df = pd.DataFrame(data = {"Year": df_raw["Year"].astype(int),"Month": df_raw["Month"].astype(int),"Day": df_raw["Day"].astype(int),"Cell": df_raw["ID"].astype(int),"Runoff": df_raw["Depth"].astype(float),"Drainage":df_raw["Drainage"].astype(float),"RSS": df_raw["Rainfall"].astype(float) + df_raw["Snowfall"].astype(float) + df_raw["Snowmelt"].astype(float) + df_raw["Irrigation"].astype(float)})
            df['Fecha'] = pd.to_datetime(df[['Year', 'Month', 'Day']])
            #Aquí se filtran por celda y por fecha
            if not sensitivity:
                self.cell = self.output.run_cell.currentText()
                if self.cell!="All cells" :
                    df = df[df.Cell==np.int64(self.cell)]
            #Aquí se filtra por fecha
            if not sensitivity:
                df = df[(df.Fecha>=date_in)&(df.Fecha<=date_fin)]
        else: #Si se ha escogido otra cosa que no sea Runoff
            #Los filtros
            self.cell = self.output.run_cell.currentText()
            if sensitivity:
                self.cell = "All cells"
            #Función para importar los datos que no son Runoff
            def dataframe_creation(path,subtotal_column, erosion = False, source = None):
                df_raw = self.df_section_output(path,delete_second=False,data_type = data_type)
                units = df_raw.columns[-1][-4:]
                subtotal_column = subtotal_column+" "+units
                if erosion:
                    df = pd.DataFrame(data = {"Year":df_raw["Year"].astype(int),"Month":df_raw["Month"].astype(int),"Day":df_raw["Day"].astype(int),"Cell":df_raw["Cell ID"].astype(str),"Source":df_raw["Source"].astype(str),"Yield":df_raw[f"Subtotals {units}"].astype(float)})
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
                if not sensitivity:
                    if self.cell!="All cells" :
                        df = df[df.Cell==np.int64(self.cell)]
                #Se pone la fecha
                df = df.assign(Fecha=pd.to_datetime(df[['Year', 'Month', 'Day']]))
                df = df.groupby('Fecha').sum(numeric_only=True).reset_index()
                df.set_index('Fecha', inplace=True)
                df = df["Yield"]
                if not sensitivity:
                    rango_fechas_deseado = pd.date_range(start=date_in, end=date_fin, freq='D')
                    df = df.reindex(rango_fechas_deseado, fill_value=0)
                return df
            #Se ponen aquí los inputs dependiendo de lo que se haya escogido
            if data_type == "Gully" or data_type == "Pond" or data_type == "Sheet & Rill" or data_type == "Subtotal":
                path =  self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Sediment_yield_(mass).csv"
                if sensitivity: #cuando se hace el análisis de sensibilidad la ruta es otra
                    path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Sediment_yield_(mass).csv"
                column_name = "Subtotals"
                try:
                    df = dataframe_creation(path,column_name,erosion = True, source = data_type)
                except:
                    self.warning_message(f"{path} has not a correct format")
                    self.error = True
                    return
            if data_type == "Nitrogen":
                path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Nitrogen_yield_(mass).csv"
                if sensitivity: #cuando se hace el análisis de sensibilidad la ruta es otra
                    path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Nitrogen_yield_(mass).csv"
                column_name = "Subtotal N"
                try:
                    df = dataframe_creation(path,column_name)
                except:
                    self.warning_message(f"{path} has not a correct format")
                    self.error = True
                    return
            if data_type == "Carbon":
                path =  self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv"
                if sensitivity: #cuando se hace el análisis de sensibilidad la ruta es otra
                    path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv"
                column_name = "Subtotal C"
                try:
                    df = dataframe_creation(path,column_name)
                except:
                    self.warning_message(f"{path} has not a correct format")
                    self.error = True
                    return
            if data_type == "Phosphorus":
                path =  self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Phosphorus_yield_(mass).csv"
                if sensitivity: #cuando se hace el análisis de sensibilidad la ruta es otra
                    path = self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_outputs"+"\\AnnAGNPS_EV_Phosphorus_yield_(mass).csv"
                column_name = "Subtotal P" 
                try:
                    df = dataframe_creation(path,column_name)
                except:
                    self.warning_message(f"{path} has not a correct format")
                    self.error = True
                    return
        return df
    
    def output_month(self):
        #Método para que aparezca por mes de lo que se esté pidiendo (escorrentía, erosión o nutrientes)
        #Si no se ha elegido la carpeta correcta entonces que pare el código
        if not self.file_exist:
            return
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Primero se crean los datos necesarios
        if self.data_type == "Runoff":
            #Esto se hace porque la escorrentía de la cuenca es la media ponderada con el área de las escorrentías de las celdas
            df['Runoff_Ponderado'] = df['Runoff'] * df['Drainage']
            df['RSS_Ponderado'] = df['RSS'] * df['Drainage']
            result = df.groupby('Fecha').agg({'Runoff_Ponderado': 'sum', 'Drainage': 'sum', 'RSS_Ponderado': 'sum'}).reset_index()
            result['Runoff'] = result['Runoff_Ponderado'] / result['Drainage']
            result['RSS'] = result['RSS_Ponderado'] / result['Drainage']
            df_graph = result[['Fecha', 'Runoff', 'RSS']]
            df_graph.set_index('Fecha', inplace=True)
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
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            ax1.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
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
        #Si no se ha elegido la carpeta correcta entonces que pare el código
        if not self.file_exist:
            return
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Primero se crean los datos necesarios
        if self.data_type == "Runoff":
            #Esto se hace porque la escorrentía de la cuenca es la media ponderada con el área de las escorrentías de las celdas
            df['Runoff_Ponderado'] = df['Runoff'] * df['Drainage']
            df['RSS_Ponderado'] = df['RSS'] * df['Drainage']
            result = df.groupby('Fecha').agg({'Runoff_Ponderado': 'sum', 'Drainage': 'sum', 'RSS_Ponderado': 'sum'}).reset_index()
            result['Runoff'] = result['Runoff_Ponderado'] / result['Drainage']
            result['RSS'] = result['RSS_Ponderado'] / result['Drainage']
            df_graph = result[['Fecha', 'Runoff', 'RSS']]
            df_graph.set_index('Fecha', inplace=True)
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
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            ax1.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
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
                ax0.annotate(f'{height:,.2f}', 
                             xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom',weight = "bold",size = 12)            
            # Agregar etiquetas de valores encima de las barras en ax1
            for rect in bar1:
                height = rect.get_height()
                ax1.annotate(f'{height:,.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
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
        #Si no se ha elegido la carpeta correcta entonces que pare el código
        if not self.file_exist:
            return
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Primero se crean los datos necesarios
        if self.data_type == "Runoff":
            #Esto se hace porque la escorrentía de la cuenca es la media ponderada con el área de las escorrentías de las celdas
            df['Runoff_Ponderado'] = df['Runoff'] * df['Drainage']
            df['RSS_Ponderado'] = df['RSS'] * df['Drainage']
            result = df.groupby('Fecha').agg({'Runoff_Ponderado': 'sum', 'Drainage': 'sum', 'RSS_Ponderado': 'sum'}).reset_index()
            result['Runoff'] = result['Runoff_Ponderado'] / result['Drainage']
            result['RSS'] = result['RSS_Ponderado'] / result['Drainage']
            df_graph = result[['Fecha', 'Runoff', 'RSS']]
            df_graph.set_index('Fecha', inplace=True)
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
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            ax1.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
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
                ax0.annotate(f'{height:,.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
                             xytext=(0, 3), textcoords="offset points",
                             ha='center', va='bottom',weight = "bold",size = 12)

            # Agregar etiquetas de valores encima de las barras en ax1
            for rect in bar1:
                height = rect.get_height()
                ax1.annotate(f'{height:,.2f}', xy=(rect.get_x() + rect.get_width() / 2, height),
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
        #Si no se ha elegido la carpeta correcta entonces que pare el código
        if not self.file_exist:
            return
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #Se crean los dataframes dependiendo de si se ha filtrado la celda
        if self.data_type == "Runoff":
            #Esto se hace porque la escorrentía de la cuenca es la media ponderada con el área de las escorrentías de las celdas
            df['Runoff_Ponderado'] = df['Runoff'] * df['Drainage']
            df['RSS_Ponderado'] = df['RSS'] * df['Drainage']
            result = df.groupby('Fecha').agg({'Runoff_Ponderado': 'sum', 'Drainage': 'sum', 'RSS_Ponderado': 'sum'}).reset_index()
            result['Runoff'] = result['Runoff_Ponderado'] / result['Drainage']
            result['RSS'] = result['RSS_Ponderado'] / result['Drainage']
            df_graph = result[['Fecha', 'Runoff', 'RSS']]
            df_graph.set_index('Fecha', inplace=True)
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
            table_df.iloc[:,1] = table_df.iloc[:,1].apply(lambda x: f'{x:,.2f}')
            try:
                table = ax.table(cellText=table_df.values, colLabels=table_df.columns, loc='center', cellLoc='center', colColours=['#f5f5f5'] * len(table_df.columns))
            except:
                iface.messageBar().pushMessage("No day with value higher than 0",level=Qgis.Warning)
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
        #Si no se ha elegido la carpeta correcta entonces que pare el código
        if not self.file_exist:
            return
        #Se importan los datos
        df = self.import_df(self.data_type)
        if self.error:
            self.error = False
            return
        #SE CREA DE EVOLUCIÓN GRÁFICO
        #Se crean los dataframes dependiendo de si se ha filtrado la celda
        if self.data_type == "Runoff":
            #Esto se hace porque la escorrentía de la cuenca es la media ponderada con el área de las escorrentías de las celdas
            df['Runoff_Ponderado'] = df['Runoff'] * df['Drainage']
            df['RSS_Ponderado'] = df['RSS'] * df['Drainage']
            result = df.groupby('Fecha').agg({'Runoff_Ponderado': 'sum', 'Drainage': 'sum', 'RSS_Ponderado': 'sum'}).reset_index()
            result['Runoff'] = result['Runoff_Ponderado'] / result['Drainage']
            result['RSS'] = result['RSS_Ponderado'] / result['Drainage']
            df_graph = result[['Fecha', 'Runoff', 'RSS']]
            df_graph.set_index('Fecha', inplace=True)
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
            #Separador de miles de eje y 
            def format_with_commas(x, pos):
                return f'{x:,.0f}'
            ax0.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            ax1.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
            ax2.yaxis.set_major_formatter(FuncFormatter(format_with_commas))
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
            #Quitar grids
            ax2.grid(False)
            ax2.grid(False)
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
                self.file_exist = True
                
            else:
                #Se cambia el icono
                path_icon = os.path.join(self.plugin_directory, "images/no_file.svg")
                self.output.file_ex.setIcon(QIcon(path_icon))
                if self.output.lineEdit.text()!="":
                    self.output.label_9.setText(f"NEXT STEP: the folder you have selected does not contain the {file} file.It is necessary to make a execution where the {column} column of the {input_file} file is set to T.")
                else:
                    self.output.label_9.setText(f"NEXT STEP: select the folder in which {file} is located.")
                self.file_exist = False
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
        
    def df_section_output(self,fichero,delete_second =False,data_type=False):
        #Método que se utiliza para obtener el dataframe de los resultados para crear los gráficos
        if not data_type:
            data_type = self.data_type
        if data_type == "Runoff":
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
            if self.data_type=="Runoff":
                path = self.output.lineEdit.text()+"\\AnnAGNPS_SIM_Insitu_Soil_Moisture_Daily_Cell_Data.csv"
            if self.data_type == "Subtotal" or self.data_type == "Gully" or self.data_type == "Pond" or self.data_type == "Sheet & Rill":
                path = self.output.lineEdit.text()+"\\AnnAGNPS_EV_Sediment_yield_(mass).csv"
            if self.data_type=="Nitrogen":
                path = self.output.lineEdit.text()+"\\AnnAGNPS_EV_Nitrogen_yield_(mass).csv"
            if self.data_type=="Carbon":
                path = self.output.lineEdit.text()+"\\AnnAGNPS_EV_Organic_Carbon_yield_(mass).csv"
            if self.data_type=="Phosphorus":
                path = self.output.lineEdit.text()+"\\AnnAGNPS_EV_Phosphorus_yield_(mass).csv"
            #Se importan los datos
            df_raw = self.df_section_output(path,delete_second=True).iloc[2:,]
            #Se ponen las celdas en el combobox
            #Primero se borran los elementos que puede haber en el combobox y luego se pone
            self.output.run_cell.clear()
            if self.data_type=="Runoff":
                cells = [str(x) for x in np.unique(df_raw.ID)]
            else:
                cells = [str(x) for x in np.unique(df_raw["Cell ID"])]
            #Esto es para quitar estos elementos que a veces están en erosión y en nutrientes
            for i in ["Bed & Bank","Landscape","Watershed"]:
                try:
                    cells.remove(i)
                except:
                    pass
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
        #Function to return the path depending if the file path is absolute or relative
        def file_input(line):
            if os.path.isabs(line.text()):
                return line.text()
            else:
                return self.dic_folder[line].text()+"/"+line.text() 
        if self.border == False:
            for i in self.lines_dialog:
                    if i.text()!="" and path.exists(file_input(i)) and i.text()!="-- Provided by TopAGNPS --":
                        i.setStyleSheet("QLineEdit {border: 3px solid #00FF00; }\n QLineEdit { background-color: rgb(196, 240, 119) ; }")
                    elif i.text()!="" and not path.exists(file_input(i)) and i.text()!="-- Provided by TopAGNPS --":
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
        for i in [self.output.pushButton_11,self.output.pushButton_13,self.output.pushButton_14,self.output.pushButton_19,self.output.pushButton_22,self.output.pushButton_20,self.output.pushButton_21,self.output.pushButton_23,self.output.pushButton_24,self.output.pushButton_25,self.output.pushButton_26,self.output.pushButton_27,self.output.pushButton_28,self.output.pushButton_29]:
            i.setIcon(QIcon(icon))
        #Add remove row in sensitivity analysis table
        self.sensitivity_dialog.add.setIcon(QIcon(os.path.join(self.plugin_directory, "images/add.svg")))
        self.sensitivity_dialog.delete_row.setIcon(QIcon(os.path.join(self.plugin_directory, "images/remove.svg")))
        #Sensitivity analysis
        self.dlg.sensitivity.setIcon(QIcon(os.path.join(self.plugin_directory, "images/balance.svg")))
        #Information of control files
        self.ctopagnps.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.cpeg.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.cagbuf.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.cagwet.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.cconcepts.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.cpothole.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.agflow.info.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        self.inputs.pushButton.setIcon(QIcon(os.path.join(self.plugin_directory, "images/documentation.svg")))
        #Open AnnAGNPS folder
        self.output.open_folder.setIcon(QIcon(os.path.join(self.plugin_directory, "images/folder.svg")))
        
        
    def url_upna(self,event):
        #Método para abrir las páginas web de la upna
        try:
            webbrowser.open("https://www.unavarra.es/portada")
        except:
            pass

    def url_usda(self,event):
        #Método para abrir las páginas web de usda
        try:
            webbrowser.open("https://www.usda.gov/")
        except:
            pass
            
    def url_github(self,event):
        #Método para abrir el repositorio de github
        try:
            webbrowser.open("https://github.com/Inigobarbe/QGIS-AnnAGNPS")
        except:
            pass
            
    def url_article(self,event):
        #Método para abrir el artículo 
        try:
            webbrowser.open("https://www.sciencedirect.com/science/article/pii/S136481522400029X")
        except:
            pass

    def topagnps_provided(self,check):
        #Método para poner si se va a usar el output de topagnps para cell, EG, reach y riparian buffer data
        dic = {self.inputs.checkBox:self.inputs.l_3,self.inputs.checkBox_2:self.inputs.l_5,self.inputs.checkBox_3:self.inputs.l_10,self.inputs.checkBox_4:self.inputs.l_41,self.inputs.checkBox_5:self.inputs.l_13}
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
        #Metod to create file with the name of existing file. If we are using the input table tool then close the dialog. 
        if not self.overwriting_input: #we are overwriting in CSV file creation mode
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
        else: #we are overwriting in table file creation mode
            self.overwrite.close()
            self.table_input_overwrite = True
            self.table_inputs(self.button)
            self.table_input_overwrite = False
            
        
    def not_overwrite_file(self):
        #Metod to not overwriting the file if there is a file with the same name. 
        self.overwrite.close()
    
    def change_icons(self,linea):
        #Método para cambiar el icono según haya o no texto en las secciones (inputs) de AnnAGNPS.
        if linea.text()!="":
            self.inverted_dict[linea].setIcon(QIcon(self.icon_path_document))
            self.inverted_dict[linea].setToolTip(self.tr("Open CSV file"))
        else:
            self.inverted_dict[linea].setIcon(QIcon(self.icon_path_createdocument))
            self.inverted_dict[linea].setToolTip(self.tr("Create CSV file"))
            
    def open_file(self,boton):
        #Método para que se abra el archivo que contiene los datos de las secciones de AnnAGNPS
        if self.dic_botones[boton].text()!="":
            try:
                if self.dic_botones[boton].text()=="-- Provided by TopAGNPS --":
                    file_path = self.direccion+"\\Preprocessing_inputs"+"\\"+os.path.basename(self.file_input(self.dic_botones[boton]))
                    if os.path.exists(file_path):
                        os.startfile(file_path)
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
        #Método para que cuando se seleccione el DEM ya se tenga en todo el código la dirección y el epsg. También se ponen la dirección de las carpetas en el diálogo de los outputs y se asigna el nombre del dem en Topagnps.csv. 
        if self.dlg.comboBox.currentIndex() >=1:
            try:
                self.epsg = QgsProject.instance().crs().authid()
                #Se crean las variables con los datos de la capa
                all_layers = QgsProject.instance().layerTreeRoot().children()
                layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
                selectedLayerIndex = self.dlg.comboBox.currentIndex()-1
                selectedLayer = layers[selectedLayerIndex].layer()
                self.fichero_mdt =  selectedLayer.dataProvider().dataSourceUri()
                try:
                    self.epsg_dem = selectedLayer.crs().authid().split(":")[1]
                except:
                    self.epsg_dem = "No defined"
                    
                dir_mdt, self.name_mdt = os.path.split(self.fichero_mdt)
                #Si no existe la carpeta de preprocessing inputs entonces se crea
                self.create_preprocessing_inputs_folder()
                #Add name of DEM to Topagnps.csv if this file exists
                if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV"):
                    topagnps_control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV",encoding = "ISO-8859-1",delimiter=",")
                    topagnps_control_file["FILENAME"].iloc[0]=self.name_mdt
                    topagnps_control_file.to_csv(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV", index=False, float_format='%.5f')
                else:
                    control_file = pd.DataFrame(data = {"FILENAME":[self.name_mdt],"FORMAT":"",
                                    "DEMPROC":"","OUTFORMAT":"","OUTROW":"","OUTCOL":"","CSA":"","MSCL":"",
                                    "UTME":"","UTMN":"","ROWS":"","COLS":"","CELLSIZE":"","NODATA":"",
                                    "OUTSNAP":"","DNMCNT":"","DEMEDGE":"","VERBOSE":"",
                                    "KEEPFILES":"","OPTIMIZE":"","MODULE":"","OUTPUT":"",
                                    "READOUT":"","READPATH":""})
                    control_file.to_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"TOPAGNPS.csv", index=False, float_format='%.5f')
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
        layer_name = self.dlg.cbSoil.currentText()
        if selectedLayerIndex >=0:
            try:
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
                selectedLayer = next((layer for layer in layers if layer.name() == layer_name), None)
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
        layer_name = self.dlg.cbMan.currentText()
        if selectedLayerIndex >=0:
            try:
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
                selectedLayer = next((layer for layer in layers if layer.name() == layer_name), None)
                fields = selectedLayer.fields()
                field_names = [field.name() for field in fields]
                self.dlg.cbColumnMan.addItems(field_names)
                self.management_field_names = field_names
            except:
                pass
                
    def buffer_nombre(self):
        #Asignar en el control file de AGBUF el nombre del archivo que se ha seleccionado en el plugin como el buffer
        try:
            if self.dlg.comboBox_2.currentIndex()>0:
                if path.exists(self.direccion+"\\Preprocessing_inputs"+"/AGBUF.csv"):
                    all_layers = QgsProject.instance().layerTreeRoot().children()
                    layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
                    selectedLayerIndex = self.dlg.comboBox_2.currentIndex()-1
                    selectedLayer = layers[selectedLayerIndex].layer()
                    self.fichero_buf =  selectedLayer.dataProvider().dataSourceUri()
                    buffer_directory, self.name_buffer  = os.path.split(self.fichero_buf)
                    control = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"/AGBUF.csv",encoding = "ISO-8859-1",delimiter=",")
                    nombre_buffer_control = control.columns[[x.lower() for x in control.columns].index("buffer")]#esto es para poner cómo se llama el buffer en el control file
                    control[nombre_buffer_control].iloc[0]=self.name_buffer
                    control.to_csv(self.direccion+"\\Preprocessing_inputs"+"/AGBUF.csv", index=False, float_format='%.5f')
                    
        except IndexError: #si el error es de que no hay capas en el canvas y se añade desde fichero y es index error entonces pasa, pero si es otro tipo de error entonces no. 
            pass
        except Exception as e:
            raise e
        
    def vegetation_nombre(self):
        #Asignar en el control file de AGBUF el nombre del archivo que se ha seleccionado en el plugin como el vegetation   
        try:
            if self.dlg.comboBox_3.currentIndex()>0:
                if path.exists(self.direccion+"\\Preprocessing_inputs"+"/AGBUF.csv"):
                    all_layers = QgsProject.instance().layerTreeRoot().children()
                    layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
                    selectedLayerIndex = self.dlg.comboBox_3.currentIndex()-1
                    selectedLayer = layers[selectedLayerIndex].layer()
                    self.fichero_veg =  selectedLayer.dataProvider().dataSourceUri()
                    vegetation_directory, self.name_vegetation  = os.path.split(self.fichero_veg)
                    control = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"/AGBUF.csv",encoding = "ISO-8859-1",delimiter=",")
                    nombre_veg_control = control.columns[[x.lower() for x in control.columns].index("vegetation")]#esto es para poner cómo se llama el vegetation en el control file
                    control[nombre_veg_control].iloc[0]=self.name_vegetation
                    control.to_csv(self.direccion+"\\Preprocessing_inputs"+"/AGBUF.csv", index=False, float_format='%.5f')
        except IndexError: #si el error es de que no hay capas en el canvas y se añade desde fichero y es index error entonces pasa, pero si es otro tipo de error entonces no. 
            pass
        except Exception as e:
            raise e

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
        self.end_execution = 0 #si es igual a 1 entonces se para el análisis de sensibilidad

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = Dialog_Base()
        # Fetch the currently loaded layers
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
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
        self.dlg.raise_()
        self.dlg.activateWindow()
        self.ejecucion_condicion=0
        
    def ejecuciones(self):
        #Método para las ejecuciones
        self.end_execution = 0
        
        #Error if folder was not selected
        if not hasattr(self,"direccion"):
            self.warning_message("Please select a working directory before executing")
            return
        #Error if name of project not selected
        if self.dlg.name_of_project.text() == "":
            self.warning_message("Please select the name of the project before executing")
            return
        
        #Ejecutar
        self.ejecucion_completa()
            
    def ejecucion_completa(self):
        #Esta función es en donde se ejecuta el modelo
        
        #Add project directory
        self.direccion = str(self.dlg.project.text())+"\\"+self.dlg.name_of_project.text()
        
        #Primero se establece la variable que contiene las capas del proyecto
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        
        #Establecer directorio de DEM y EPSG del proyecto
        #Solo se hace una vez. Es decir, si elijo outlet solo se elige en la primera ronda. Sino el selected layer puede cambiar de DEM a los reaches y da error después.
        if not self.dlg.checkBox_2.isChecked() or (self.dlg.checkBox_2.isChecked() and not self.segunda_ronda):
            #Se elige aquí otra vez porque igual cuando se había seleccionado el proyecto estaba en otro epsg
            epsg = QgsProject.instance().crs().authid()
            self.epsg = epsg
            
            #Se cambia de directorio al directorio del proyecto y se establece el directorio donde están los ejecutables
            self.executable_directory  = self.plugin_dir+"\\Executables"            
        
        #EJECUCIÓN DE TOPAGNPS
        if self.dlg.cbTop.isChecked():
            #Se crea la carpeta de Preprocessing_inputs si no estaba creada. Ahí se meten los inputs y se ejecuta TopAGNPS y luego los outputs se meten a Preprocessing_outputs
            
            
            #Una vez creada se meten todos los archivos en esa carpeta
            self.create_folder_preprocessing_and_move_files()
            
            #Se pone el epsg del proyecto
            self.epsg = QgsProject.instance().crs().authid()
            
            #Función para que se le diga el nombre del archivo y te devuelva la dirección completa
            def fichero(nombre):
                return self.direccion+"\\Preprocessing_inputs"+"\\"+nombre
            
            #Dar error si no existe el archivo TOPAGNPS.CSV
            if not os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV"):
                iface.messageBar().pushMessage("Error Input data", "Control file of TopAGNPS, TOPAGNPS.CSV, not found" ,level=Qgis.Warning)
                self.end_execution = 1
                return
            #Si el formato de la columna FILENAME no es str entonces dar error
            topagnps_control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV",encoding = "ISO-8859-1",delimiter=",")
            if type(topagnps_control_file["FILENAME"].iloc[0])!=str:
                iface.messageBar().pushMessage("Error Input data", "Please select a correct FILENAME in TOPAGNPS.CSV" ,level=Qgis.Warning)
                self.end_execution = 1
                return
            
            #Si se ha elegido poner coordenadas automáticamente entonces hay que hacer que TopAGNPS haga sólo DEM elevation preprocessing and full network generation
            if self.dlg.checkBox_2.isChecked() and not self.segunda_ronda:
                topagnps_control_file = pd.read_csv(fichero("TOPAGNPS.csv"),encoding = "ISO-8859-1",delimiter=",")
                topagnps_control_file["DEMPROC"].iloc[0] = "2" #se pone en texto porque sino se guarda en decimal y da error.
                topagnps_control_file.to_csv(fichero("TOPAGNPS.csv"), index=False, float_format='%.5f')
            
            
            #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
            self.time_start_preprocessing = datetime.now()
            
            
            #EJECUCIÓN DE TOPAGNPS            
            def main():
                f = open(self.executable_directory+"\\"+"EjecutarTopagnps.bat","w+")
                linea_uno = "CD /d {}".format(self.direccion+"\\Preprocessing_inputs")
                linea_dos = r"CALL {}\TopAGNPS_v6.00.a.025_release_64-bit.exe".format(self.executable_directory)
                f.write("{} \n".format(linea_uno))
                f.write("{} \n".format(linea_dos))
                f.close()
            main()
            subprocess.call(self.executable_directory+"\\"+"EjecutarTopagnps.bat")
            #proc = subprocess.Popen(self.executable_directory+"\\"+"EjecutarTopagnps.bat", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            #stdout, stderr = proc.communicate()
            
            #If error file of TopAGNPS is opened, then return a error message
            try:
                open(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.csv", "r+") 
            except PermissionError:
                iface.messageBar().pushMessage("Error TopAGNPS","Close TOPAGNPS_err.csv before the start of execution",level=Qgis.Warning,duration = 10)
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder()
                self.end_execution = 1
                return
            except:
                pass

            #Cuando se eligen coordenadas automáticamente con el plugin primero se ejecuta Topagnps y da error (se ejecuta la primera para poner el reaches en QGIS) osea que no queremos que python salte si hay error en la primera ronda. Queremos que salte python cuando hay error y si se ha seleccionado que no se elige automaticamente. O sino cuando hay error y se ha elegido automáticamente pero la segunda ejecución de Topagnps da error. 
            if os.path.isfile(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.CSV") and os.path.getsize(self.direccion+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.CSV")>0 and (not self.dlg.checkBox_2.isChecked() or self.segunda_ronda):
                self.end_execution = 1
                error = pd.read_csv(fichero("TOPAGNPS_err.CSV"),encoding = "ISO-8859-1",delimiter=",")
                iface.messageBar().pushMessage("Error TOPAGNPS", error.columns[3],level=Qgis.Warning,duration = 10)
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder()
                #Se abre el archivo de errores
                try:
                    os.startfile(self.direccion+"\\Preprocessing_outputs"+"\\TopAGNPS_err.csv")
                except:
                    pass
                #Este return es para parar el codigo
                return
            
            #Función para cambiar de coordenadas
            def change_coordinates(filename,outputname):
                input_raster = gdal.Open(fichero(filename))
                output_raster = fichero(outputname)
                warp = gdal.Warp(output_raster,input_raster,dstSRS=self.epsg)
                warp = None # Closes the files
            #Esto es para cambiar las coordenadas del outlet en TOPAGNPS.csv. Para ello se tiene que estar en primera ronda y se tiene que haber elegido la opción de escoger el outlet automáticamente. 
            if self.dlg.checkBox_2.isChecked() and not self.segunda_ronda:
                if self.ejecucion_condicion == 0:
                    #Add coordinates to topagnps control file
                    try:
                        self.add_coordinates_to_topagnps_control_file()
                    except Exception as e:
                        #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                        self.save_files_preprocessing_in_folder()
                        self.iface.messageBar().pushMessage(str(e),level=Qgis.Info)
                        return
                    #Return porque dentro del add_coordinates_to_topagnps_control_file ya se ejecuta de nuevo y no hay que seguir con el código
                    return
            self.segunda_ronda = False
            #VALORES DEL TAMAÑO DE PIXEL
            layer = QgsRasterLayer(topagnps_control_file["FILENAME"].iloc[0],"dednm")
            self.pixelSizeX = round(layer.rasterUnitsPerPixelX(),2)
            self.pixelSizeY = round(layer.rasterUnitsPerPixelY(),2)
            
            #ASIGNAR LOS VALORES DE SUELO Y MANEJO A AnnAGNPS_Cell_Data_Section.csv
            try:
                self.add_soil_and_management_cell()
            except Exception as e:
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder()
                self.warning_message(str(e))
                return
            
            
            #Mensaje de éxito si se ha ejecutado TOPAGNPS con éxito si no se ha escogido ejecutar AnnAGNPS
            if not self.dlg.cbAnn.isChecked() and ((not self.dlg.checkBox_2.isChecked() and self.ejecucion_condicion == 0)or (self.dlg.checkBox_2.isChecked() and self.ejecucion_condicion == 1)):
                self.warning_message("Preprocessing executed succesfully!")
            #Mensaje para que selecciones las coordenadas
            if not self.dlg.cbAnn.isChecked() and self.dlg.checkBox_2.isChecked() and self.ejecucion_condicion == 0:
                self.iface.messageBar().pushMessage("Coordinate selection", "Please move the mouse to the outlet and click on it",level=Qgis.Info)
            
            #If add outlet automatically was checked, then uncheck
            if self.dlg.checkBox_2.isChecked(): self.dlg.checkBox_2.setChecked(False)
            
            #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
            self.save_files_preprocessing_in_folder()
            
            
        #EJECUCIÓN DE ANNAGNPS
        if self.dlg.cbAnn.isChecked():
            
            #Se crea la carpeta de Preprocessing_inputs si no estaba creada. Ahí se meten los inputs y se ejecuta TopAGNPS y luego los outputs se meten a Preprocessing_outputs
            #Una vez creada se meten todos los archivos en esa carpeta
            self.create_folder_processing_and_move_files()
            
            #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
            self.time_start_processing = datetime.now()
            
            
            #EJECUCIÓN DE ANNAGNPS
            #os.chdir(self.direccion+"\\"+directory)
            def execute_bat():
               def main():
                   f = open(self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat","w+")
                   linea_uno = "CD /d {}".format(self.direccion+"\\Processing_inputs")
                   linea_dos = r"CALL {}\AnnAGNPS_v6.00.r.058_release_64-bit.exe".format(self.executable_directory)
                   f.write("{} \n".format(linea_uno))
                   f.write("{} \n".format(linea_dos))
                   f.close()
               main()
            execute_bat()
            r'''env = os.environ.copy()
            env['PATH'] = f'{self.executable_directory};' + env['PATH']
            command = self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat"
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='latin-1', env=env)'''

            subprocess.call(self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat")

            
            #If error file of AnnAGNPS is opened, then return a error message
            try:
                open(self.direccion+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv", "r+") 
            except PermissionError:
                iface.messageBar().pushMessage("Error AnnAGNPS","Close AnnAGNPS_LOG_Error.csv before the start of execution",level=Qgis.Warning,duration = 10)
                self.end_execution = 1
                return
            except:
                pass
                        
            #PONER MENSAJE DE ERROR SI ANNAGNPS FUNCIONA MAL
            time.sleep(1)
            if path.exists(self.direccion+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv"):
                if os.stat(self.direccion+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv").st_size>0:
                    self.end_execution =1
                    try:
                        text = open(self.direccion+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv", "r")
                        text = ''.join([i for i in text]) 
                        text = text.replace("\"", "/") 
                        texto = text.splitlines()
                        txt = texto[2].split(",")[-1]
                        iface.messageBar().pushMessage("Error AnnAGNPS",txt,level=Qgis.Warning,duration = 10)
                    except:
                        pass
                    
                    self.end_execution = 1
                    #Se abre el archivo de errores
                    try:
                        os.startfile(self.direccion+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv")
                    except:
                        pass
                    #Este return es para parar el codigo
                    return 
            
            #EJECUCIÓN DEL OUTPUT_TABLES
            time.sleep(1)
            shutil.copyfile(self.executable_directory + "\\" +"STEAD.fil" ,self.direccion + "\\Processing_inputs\\" +"STEAD.fil")
            os.chdir(self.direccion+"\\Processing_inputs")
            proc = subprocess.Popen(self.executable_directory + "\\" +"STEAD.exe", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            
            #Los outputs de AnnAGNPS se guardan en Processing_outputs
            self.save_files_processing_in_folder()
            
            #Warning message
            self.warning_message("Processing executed succesfully!")
            
            
        
    def add_coordinates_to_topagnps_control_file(self):
        """Method to add coordinates to TOPAGNPS control file"""
        def fichero(nombre):
            return self.direccion+"\\Preprocessing_inputs"+"\\"+nombre
        def change_coordinates(filename,outputname):
            input_raster = gdal.Open(fichero(filename))
            output_raster = fichero(outputname)
            warp = gdal.Warp(output_raster,input_raster,dstSRS=self.epsg)
            warp = None # Closes the files
        #Primero, si no existe "NETFUL.asc" entonces ha dado error TOPAGNPS y hay que para la ejecución. Si no se para antes es porque le he dicho que no pare porque el hecho de no poner coordenadas daba error.
        if not os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\NETFUL.asc"):
            self.end_execution = 1
            error = pd.read_csv(fichero("TOPAGNPS_err.CSV"),encoding = "ISO-8859-1",delimiter=",")
            #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
            self.save_files_preprocessing_in_folder()
            #Se abre el archivo de errores
            try:
                os.startfile(self.direccion+"\\Preprocessing_outputs"+"\\TopAGNPS_err.csv")
            except:
                pass
            #Este return es para parar el codigo
            raise Exception("Error in preprocessing"+str(error.columns[3]))
        
        change_coordinates("NETFUL.asc","NETFUL_epsg.asc")
        layer = QgsRasterLayer(fichero("NETFUL_epsg.asc"),"reaches")
        QgsProject.instance().addMapLayer(layer)
        #Esto es para que se desactiven el resto de las capas y se pueda ver la capa reaches
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if child.name() != "reaches":
                child.setItemVisibilityChecked(False)
        iface.mapCanvas().refresh()
        
        #Close dialog
        self.dlg.close()
        
        #Se ejecuta el método para las coordenadas
        self.set_coordinates()
        
        #Open again dialog
        self.dlg.show()
    
    def add_soil_and_management_cell(self):
        """Method to add soil type and management to cell"""
        def fichero(nombre):
            return self.direccion+"\\Preprocessing_inputs"+"\\"+nombre
        #A esta función le das la capa de celdas y la que se superpone (tipo de suelo o uso) y devuelve el diccionario en el que se muestra a cada celda que valor (de suelo o de uso) le corresponde
        def aplicar(fichero_celdas,fichero_superponer, columna_tipo,numero):
            numero = str(numero) #esto es porque no deja sobreescribir y tengo que crear otra capa por cada ejecución de sensibilidad
            fichero_cell = fichero_celdas
            fichero_suelo = fichero_superponer
            #Esta función devuelve un diccionario en donde a cada suelo/uso se le asigna un numero entero y luego en la capa (de suelos o uso) a cada suelo/uso se le añade el valor del diccionario
            def create_fid(file_layer):
                layer = file_layer
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
            e = processing.run("native:reprojectlayer", 
                {'INPUT':fichero_suelo,
                'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                'OPERATION':'+proj=noop','OUTPUT':QgsProcessing.TEMPORARY_OUTPUT})
            #Reproyectar celdas al epsg del proyecto
            a = processing.run("gdal:warpreproject", 
                {'INPUT':fichero(fichero_cell),
                'SOURCE_CRS':None,'TARGET_CRS':QgsCoordinateReferenceSystem('{}'.format(self.epsg)),
                'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,
                'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OUTPUT':QgsProcessing.TEMPORARY_OUTPUT})
            #Con esto se tiene el diccionario que te asigna para cada suelo/uso un valor numérico
            dic_conv = create_fid(e["OUTPUT"])
            #Rasterizar la capa de suelos
            processing.run("gdal:rasterize", 
                {'INPUT':e["OUTPUT"],
                'FIELD':'id_prueba','BURN':0,'USE_Z':False,'UNITS':1,'WIDTH':self.pixelSizeX,
                'HEIGHT':self.pixelSizeY,'EXTENT':None,'NODATA':0,'OPTIONS':'','DATA_TYPE':4,'INIT':None,
                'INVERT':False,'EXTRA':'','OUTPUT':fichero("suelo_ras.tif")})
            #Vectorizar la capa de celdas
            c = processing.run("grass7:r.to.vect", {'input':a["OUTPUT"],
                'type':2,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':QgsProcessing.TEMPORARY_OUTPUT,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})
            #Corregir geometrías porque luego sino en unión da error 
            d = processing.run("native:fixgeometries", 
                {'INPUT':c["output"],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT})    
            #Se unen las capas de celdas de celdas con las de suelo/uso
            processing.run("native:union", 
            {'INPUT':d["OUTPUT"],
            'OVERLAY':e["OUTPUT"],
            'OVERLAY_FIELDS_PREFIX':'','OUTPUT':fichero("union_capas{}_{}.gpkg".format(numero,self.numero_ejecucion))})
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
            create_attribute("union_capas{}_{}.gpkg".format(numero,self.numero_ejecucion),"$area","area_zona")
            
            #Ahora se ve qué área de suelo/uso es la mayor para cada celda y esa será la que se escoja
            layer = QgsVectorLayer(fichero("union_capas{}_{}.gpkg".format(numero,self.numero_ejecucion)),"union")
            tres_valores = []
            valores_unicos_celdas = []
            valores_unicos_suelos=[]
            for f in layer.getFeatures():
                        tres_valores.append((f["value"],f["id_prueba"],f["area_zona"]))
                        valores_unicos_celdas.append(f["value"])
                        valores_unicos_suelos.append(f["id_prueba"])
            valores_unicos_celdas = list(np.unique(valores_unicos_celdas))
            valores_unicos_suelos=list(np.unique(valores_unicos_suelos))
            valores_unicos_celdas=[x for x in valores_unicos_celdas if isinstance(x, (int, float))]
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
        annagnps_cell_data = pd.read_csv(fichero("AnnAGNPS_Cell_Data_Section.csv"),encoding = "ISO-8859-1",delimiter=",")
        #Dar error si no se ha elegido ni capa de suelos ni se ha puesto un suelo único
        if str(self.dlg.lineEdit.text())=="":
            if self.dlg.cbSoil.currentIndex()==0:
                self.end_execution = 1
                self.warning_message("Error with soil layer\nNo soil layer has been selected")
                return
            #Se aplica el suelo al fichero de cells
            try:
                suelos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_soil,self.soil_field_names[self.dlg.cbColumnSoil.currentIndex()],1)
            except:
                self.end_execution = 1
                if self.epsg_dem != self.epsg_soil:
                    raise Exception(f"Error with soil layer: The DEM and the soil layer have to overlap\nThe Coordinate Reference System of the soil layer is {self.epsg_soil} and that of the DEM is {self.epsg_dem}")
                    
                else:
                    raise Exception(f"Error with soil layer: The DEM and the soil layer have to overlap")
                    

            annagnps_cell_data["Soil_ID"] = [suelos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            #Se aplica el suelo al fichero de cárcavas efímeras, si existe el archivo PEG.csv
            if path.exists(fichero("PEG.csv")):
                eg_path = fichero(self.ephemeral_gully_file()) #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
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
                
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    annagnps_eg_data["Soil_ID"]= [dic_conv[x] for x in suelos_eg]
                except:
                    self.end_execution = 1
                    raise Exception( "Error soil map\nThe soil type layer may not cover the full extent of the watershed")
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
                
            
        #Dar error si no se ha elegido ni capa de usos ni se ha puesto un uso único
        if str(self.dlg.lineEdit_2.text())=="":
            if self.dlg.cbMan.currentIndex()==0:
                self.end_execution = 1
                self.warning_message("Error with soil management\nNo management layer has been selected.")
                return
            try:
                manejos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_manag,self.management_field_names[self.dlg.cbColumnMan.currentIndex()],2)
            except:
                self.end_execution = 1
                if self.epsg_dem != self.epsg_manag:
                    raise Exception(f"Error with management layer: The DEM and the management layer have to overlap\nThe Coordinate Reference System of the management layer is {self.epsg_manag} and that of the DEM is {self.epsg_dem}")
                    
                else:
                    raise Exception(f"Error with management layer: The DEM and the management layer have to overlap")
                
                    
            
            annagnps_cell_data["Mgmt_Field_ID"] = [manejos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            #Se aplica el uso al fichero de cárcavas efímeras
            if path.exists(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
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
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    lista_tipos = []
                    for eg_soil_i,eg_soil_k in enumerate([dic_conv[x] for x in suelos_eg]):
                        if annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="BUFFER" or annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="WETLAND":
                            lista_tipos.append(annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i])
                        else:
                            lista_tipos.append(eg_soil_k)
                    annagnps_eg_data["Mgmt_Field_ID"]= lista_tipos
                except:
                    self.end_execution = 1
                    raise Exception("Error soil use map\nThe soil use layer may not cover the full extent of the watershed")
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
            
        #Si se ha puesto un suelo único entonces se añade a todas las celdas
        if str(self.dlg.lineEdit.text())!="":
            annagnps_cell_data["Soil_ID"] =str(self.dlg.lineEdit.text())
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
        #Si se ha puesto un uso único entonces se añade a todas las celdas
        if str(self.dlg.lineEdit_2.text())!="":
            annagnps_cell_data["Mgmt_Field_ID"]=str(self.dlg.lineEdit_2.text())
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
    
    
    def add_soil_and_management_cell_sensitivity(self):
        """Method to add soil type and management to cell"""
        def fichero(nombre):
            return self.direccion_sensitivity+"\\Preprocessing_inputs"+"\\"+nombre
        #A esta función le das la capa de celdas y la que se superpone (tipo de suelo o uso) y devuelve el diccionario en el que se muestra a cada celda que valor (de suelo o de uso) le corresponde
        def aplicar(fichero_celdas,fichero_superponer, columna_tipo,numero):
            numero = str(numero) #esto es porque no deja sobreescribir y tengo que crear otra capa por cada ejecución de sensibilidad
            fichero_cell = fichero_celdas
            fichero_suelo = fichero_superponer
            #Esta función devuelve un diccionario en donde a cada suelo/uso se le asigna un numero entero y luego en la capa (de suelos o uso) a cada suelo/uso se le añade el valor del diccionario
            def create_fid(file_layer):
                layer = file_layer
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
            e = processing.run("native:reprojectlayer", 
                {'INPUT':fichero_suelo,
                'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg_sensitivity),
                'OPERATION':'+proj=noop','OUTPUT':QgsProcessing.TEMPORARY_OUTPUT})
            #Reproyectar celdas al epsg del proyecto
            a = processing.run("gdal:warpreproject", 
                {'INPUT':fichero(fichero_cell),
                'SOURCE_CRS':None,'TARGET_CRS':QgsCoordinateReferenceSystem('{}'.format(self.epsg_sensitivity)),
                'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,
                'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OUTPUT':QgsProcessing.TEMPORARY_OUTPUT})
            #Con esto se tiene el diccionario que te asigna para cada suelo/uso un valor numérico
            dic_conv = create_fid(e["OUTPUT"])
            #Rasterizar la capa de suelos
            processing.run("gdal:rasterize", 
                {'INPUT':e["OUTPUT"],
                'FIELD':'id_prueba','BURN':0,'USE_Z':False,'UNITS':1,'WIDTH':self.pixelSizeX,
                'HEIGHT':self.pixelSizeY,'EXTENT':None,'NODATA':0,'OPTIONS':'','DATA_TYPE':4,'INIT':None,
                'INVERT':False,'EXTRA':'','OUTPUT':fichero("suelo_ras.tif")})
            #Vectorizar la capa de celdas
            c = processing.run("grass7:r.to.vect", {'input':a["OUTPUT"],
                'type':2,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':QgsProcessing.TEMPORARY_OUTPUT,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})
            #Corregir geometrías porque luego sino en unión da error 
            d = processing.run("native:fixgeometries", 
                {'INPUT':c["output"],
                'OUTPUT':QgsProcessing.TEMPORARY_OUTPUT})    
            #Se unen las capas de celdas de celdas con las de suelo/uso
            processing.run("native:union", 
            {'INPUT':d["OUTPUT"],
            'OVERLAY':e["OUTPUT"],
            'OVERLAY_FIELDS_PREFIX':'','OUTPUT':fichero("union_capas{}_{}.gpkg".format(numero,self.numero_ejecucion))})
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
            create_attribute("union_capas{}_{}.gpkg".format(numero,self.numero_ejecucion),"$area","area_zona")
            
            #Ahora se ve qué área de suelo/uso es la mayor para cada celda y esa será la que se escoja
            layer = QgsVectorLayer(fichero("union_capas{}_{}.gpkg".format(numero,self.numero_ejecucion)),"union")
            tres_valores = []
            valores_unicos_celdas = []
            valores_unicos_suelos=[]
            for f in layer.getFeatures():
                        tres_valores.append((f["value"],f["id_prueba"],f["area_zona"]))
                        valores_unicos_celdas.append(f["value"])
                        valores_unicos_suelos.append(f["id_prueba"])
            valores_unicos_celdas = list(np.unique(valores_unicos_celdas))
            valores_unicos_suelos=list(np.unique(valores_unicos_suelos))
            valores_unicos_celdas=[x for x in valores_unicos_celdas if isinstance(x, (int, float))]
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
        annagnps_cell_data = pd.read_csv(fichero("AnnAGNPS_Cell_Data_Section.csv"),encoding = "ISO-8859-1",delimiter=",")
        #Dar error si no se ha elegido ni capa de suelos ni se ha puesto un suelo único
        if self.unique_soil_sensitivity=="":
            if self.fichero_soil_sensitivity=="nan":
                self.end_execution = 1
                self.warning_message("Error with soil layer\nNo soil layer has been selected")
                return
            #Se aplica el suelo al fichero de cells
            try:
                suelos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_soil_sensitivity,self.column_soil_sensitivity,1)
            except:
                self.end_execution = 1
                raise Exception(f"Error with soil layer: The DEM and the soil layer have to overlap")
                
                

            annagnps_cell_data["Soil_ID"] = [suelos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            #Se aplica el suelo al fichero de cárcavas efímeras, si existe el archivo PEG.csv
            if path.exists(fichero("PEG.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg_sensitivity),"PEG_Points","memory")
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
                
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    annagnps_eg_data["Soil_ID"]= [dic_conv[x] for x in suelos_eg]
                except:
                    self.end_execution = 1
                    raise Exception( "Error soil map\nThe soil type layer may not cover the full extent of the watershed")
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
                
            
        #Dar error si no se ha elegido ni capa de usos ni se ha puesto un uso único
        if self.unique_use_sensitivity=="":
            if self.fichero_manag_sensitivity=="nan":
                self.end_execution = 1
                self.warning_message("Error with soil management\nNo management layer has been selected.")
                return
            try:
                manejos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_manag_sensitivity,self.column_use_sensitivity,2)
            except:
                self.end_execution = 1
                raise Exception(f"Error with management layer: The DEM and the management layer have to overlap")
                
                    
            
            annagnps_cell_data["Mgmt_Field_ID"] = [manejos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            #Se aplica el uso al fichero de cárcavas efímeras
            if path.exists(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg_sensitivity),"PEG_Points","memory")
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
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    lista_tipos = []
                    for eg_soil_i,eg_soil_k in enumerate([dic_conv[x] for x in suelos_eg]):
                        if annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="BUFFER" or annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="WETLAND":
                            lista_tipos.append(annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i])
                        else:
                            lista_tipos.append(eg_soil_k)
                    annagnps_eg_data["Mgmt_Field_ID"]= lista_tipos
                except:
                    self.end_execution = 1
                    raise Exception("Error soil use map\nThe soil use layer may not cover the full extent of the watershed")
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
            
        #Si se ha puesto un suelo único entonces se añade a todas las celdas
        if self.unique_soil_sensitivity!="":
            annagnps_cell_data["Soil_ID"] =str(self.unique_soil_sensitivity)
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
        #Si se ha puesto un uso único entonces se añade a todas las celdas
        if self.unique_use_sensitivity!="":
            annagnps_cell_data["Mgmt_Field_ID"]=str(self.unique_use_sensitivity)
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
    
    
    def create_preprocessing_inputs_folder(self):
        """Method to create preprocessing input folder if it doesn't exist"""
        #Create folder
        carpeta = self.direccion+"\\Preprocessing_inputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
    
    def save_files_preprocessing_in_folder(self):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Preprocessing_outputs if it doesn´t exist
        carpeta = self.direccion+"\\Preprocessing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        
        
        
        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.direccion+"\\Preprocessing_inputs")
        carpeta_destino = Path(carpeta)

        for f in carpeta_origen.iterdir():
            try:
                if f.is_file():
                    t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                    if t > self.time_start_preprocessing:
                        shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass
    
    
        
        
    def save_files_processing_in_folder(self):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Processing_outputs if it doesn´t exist
        carpeta = self.direccion+"\\Processing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        

        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.direccion+"\\Processing_inputs")
        carpeta_destino = Path(carpeta)
        
        archivo_excluido = Path(self.direccion) / "Processing_inputs" / "AnnAGNPS.fil"
        
        for f in carpeta_origen.iterdir():
            try:
                t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                if t > self.time_start_processing and f != archivo_excluido:
                    shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass

    def save_files_processing_in_folder_scenario(self,proyecto):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Processing_outputs if it doesn´t exist
        carpeta = self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        

        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs")
        carpeta_destino = Path(carpeta)
        
        archivo_excluido = Path(self.carpeta_guardar_proyectos) / f"{proyecto}"/ "Processing_inputs" / "AnnAGNPS.fil"
        
        for f in carpeta_origen.iterdir():
            try:
                t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                if t > self.time_start_processing and f != archivo_excluido:
                    shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass
    
    
    def create_folder_preprocessing_and_move_files(self):
        """Method to create the preprocessing folders (if they dont exist) and move the input files here"""
        #Create folder
        carpeta = self.direccion+"\\Preprocessing_inputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        
        
        #Move the files that are in the interface to this file
        #Primero los DEM
        #Se mueve el DEM a la carpeta del proyecto
        try: #si el origen y el destino son los mismos da error
            shutil.copyfile(self.fichero_mdt,self.direccion+"\\Preprocessing_inputs"+"\\"+self.name_mdt)
        except:
            pass
        #Mover el fichero de buffer la carpeta del proyecto
        try: #si el origen y el destino son los mismos da error
            shutil.copyfile(self.fichero_buf,self.direccion+"\\Preprocessing_inputs"+"\\"+self.nombre_buf)
        except:
            pass
        #Mover el fichero de vegetation la carpeta del proyecto
        try: #si el origen y el destino son los mismos da error
            shutil.copyfile(self.fichero_veg,self.direccion+"\\Preprocessing_inputs"+"\\"+self.nombre_veg)
        except:
            pass
        
        #Mover el archivo de suelo y manejo
        #Estos archivos pueden ser shp por lo que hay que coger todos los archivos asociados a ese shp
        if hasattr(self,"fichero_soil"):
            origen_base = os.path.splitext(self.fichero_soil)[0]
            archivos_asociados = glob.glob(origen_base + ".*")
            destino_dir = os.path.join(self.direccion, "Preprocessing_inputs")
            for f in archivos_asociados:
                try: #si el origen y el destino son los mismos da error
                    shutil.copy(f, destino_dir)
                except:
                    pass
        
        if hasattr(self,"fichero_manag"):
            origen_base = os.path.splitext(self.fichero_manag)[0]
            archivos_asociados = glob.glob(origen_base + ".*")
            destino_dir = os.path.join(self.direccion, "Preprocessing_inputs")
            for f in archivos_asociados:
                try: #si el origen y el destino son los mismos da error
                    shutil.copy(f, destino_dir)
                except:
                    pass
    
    
    
    def warning_message(self,message):
        """Method to put a warning message"""
        #Put text
        self.dlg_warning_message.warning.setText("\n".join(textwrap.wrap(message, width=100, break_long_words=False)))
        
        courier_font = QFont("Georgia")
        courier_font.setStyleHint(QFont.Monospace)  # Asegura el estilo monoespaciado
        courier_font.setFixedPitch(True)            # Garantiza el espaciado fijo
        courier_font.setPointSize(12)               # Ajusta el tamaño de fuente, si es necesario

        # Aplicar la fuente al QLabel
        self.dlg_warning_message.warning.setFont(courier_font)
            
        #Put to the front
        self.dlg_warning_message.setWindowFlags(
            self.dlg_warning_message.windowFlags() | Qt.WindowStaysOnTopHint
        )

        self.dlg_warning_message.show()
        self.dlg_warning_message.raise_()
        self.dlg_warning_message.activateWindow()
        #Adjust size
        self.dlg_warning_message.adjustSize()
        
    def create_folder_processing_and_move_files(self):
        """Method to create the preprocessing folders (if they dont exist) and move the input files here"""
        #Create folder
        carpeta = self.direccion+"\\Processing_inputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        
            
        #Move the files that are in the interface to this file
        #CREACIÓN DE LAS SUBCARPETAS EN DONDE SE ORGANIZARÁN LOS INPUTS
        carpetas = ["simulation","general","watershed","climate"]
        parent_dir = self.direccion +"\\Processing_inputs"
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
        checks_list= [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3,self.inputs.checkBox_4,self.inputs.checkBox_5]
        sections_list = [cell_data,ephemeral_gully,reach_data,riparian_buffer,wetland_data]
        names_list = ["AnnAGNPS_Cell_Data_Section.csv",self.ephemeral_gully_file(),"AnnAGNPS_Reach_Data_Section.csv","AnnAGNPS_Riparian_Buffer_Data_Section_AgBuf.csv","AnnAGNPS_Wetland_Data_Section.csv"]
        for i in range(len(checks_list)):
            if checks_list[i].isChecked():
                sections_list[i]=self.direccion+"\\Preprocessing_outputs"+"\\"+names_list[i]
        cell_data,ephemeral_gully,reach_data,riparian_buffer,wetland_data = sections_list
        #Función para que se le diga el nombre del archivo y te devuelva la dirección completa, en este caso para los inputs que usará AnnAGNPS
        def fichero_input(file_name,direct):
            if os.path.isabs(file_name):
                return   self.direccion+"\\Processing_inputs\\" + direct + "/" +os.path.basename(file_name)
            else:
                return self.direccion+"\\Processing_inputs\\" + direct + "/" +file_name
        
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
                    if t == climate_files and os.path.normpath(origin_direction(f,"climate"))!=os.path.normpath(fichero_input(f,"climate")):#esta última condición es porque si no hay que mover el archivo, da error
                        shutil.copyfile(origin_direction(f,"climate"),fichero_input(f,"climate"))
                except:
                    self.warning_message("Error AnnAGNPS\n{} file not found".format(origin_direction(f,"climate")))
                    self.end_execution = 1
                    return
                try:
                    if t == general_files and os.path.normpath(origin_direction(f,"general"))!= os.path.normpath(fichero_input(f,"general")):
                       shutil.copyfile(origin_direction(f,"general"),fichero_input(f,"general"))
                except:
                    self.warning_message("Error AnnAGNPS\n{} file not found".format(origin_direction(f,"general")))
                    self.end_execution = 1
                    return
                try:
                    if t == simulation_files and os.path.normpath(origin_direction(f,"simulation"))!=os.path.normpath(fichero_input(f,"simulation")):
                       shutil.copyfile(origin_direction(f,"simulation"),fichero_input(f,"simulation"))
                except:
                    self.warning_message("Error AnnAGNPS\n{} file not found".format(origin_direction(f,"simulation")))
                    self.end_execution = 1
                    return
                try:
                    if t == watershed_files and os.path.normpath(origin_direction(f,"watershed"))!=os.path.normpath(fichero_input(f,"watershed")):
                        shutil.copyfile(origin_direction(f,"watershed"),fichero_input(f,"watershed"))
                except:
                    self.warning_message("Error AnnAGNPS\n{} file not found".format(origin_direction(f,"watershed")))
                    self.end_execution = 1
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
        master.to_csv(self.direccion +"\\Processing_inputs\\" + "annagnps_master.csv", encoding='utf-8', index=False)
        
        #MOVER EL ANNAGNPS.FIL (CREO QUE ES EL CONTROL FILE DE ANNAGNPS) A LA CARPETA DE INPUTS de procesamiento
        shutil.copyfile(self.plugin_dir+"\\Executables"  + "\\" +"AnnAGNPS.fil" ,self.direccion +"\\Processing_inputs\\" +"AnnAGNPS.fil")
    
    
    
    
    def ephemeral_gully_file(self):
        #Metod to select the file name containing ephemeral gully information depending on the presence of other control files
        #Files that go from more to less information
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\"+"AGWET.csv"):
            return "AnnAGNPS_Ephemeral_Gully_Data_Section_Revised_by_AgWet.csv"
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\"+"Agbuf.csv"):
            return "AnnAGNPS_Ephemeral_Gully_Data_Section_Revised_by_AgBuf.csv"
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\"+"PEG.csv"):
            return "AnnAGNPS_Ephemeral_Gully_Data_Section.csv"

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
            return self.direccion+"\\Preprocessing_inputs"+"\\"+nombre
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
        #topagnps_control_file["FORMAT"].iloc[0] = 0
        topagnps_control_file["OUTFORMAT"].iloc[0] = str(1)
        topagnps_control_file["DEMPROC"].iloc[0] = str(0)
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
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()        
        control_file = pd.DataFrame(data = {"FILENAME":[self.ctopagnps.lineEdit_7.text()],"FORMAT":[self.ctopagnps.lineEdit_8.text()],
                                    "DEMPROC":[self.ctopagnps.lineEdit_5.text()],"OUTFORMAT":[self.ctopagnps.lineEdit_14.text()],
                                    "OUTROW":[self.ctopagnps.lineEdit_22.text()],"OUTCOL":[self.ctopagnps.lineEdit_15.text()],
                                    "CSA":[self.ctopagnps.lineEdit_3.text()],"MSCL":[self.ctopagnps.lineEdit_10.text()],
                                    "UTME":[self.ctopagnps.lineEdit_19.text()],"UTMN":[self.ctopagnps.lineEdit_20.text()],
                                    "ROWS":[self.ctopagnps.lineEdit_18.text()],"COLS":[self.ctopagnps.lineEdit_2.text()],
                                    "CELLSIZE":[self.ctopagnps.lineEdit.text()],"NODATA":[self.ctopagnps.lineEdit_11.text()],
                                    "OUTSNAP":[self.ctopagnps.lineEdit_17.text()],"DNMCNT":[self.ctopagnps.lineEdit_6.text()],
                                    "DEMEDGE":[self.ctopagnps.lineEdit_4.text()],"VERBOSE":[self.ctopagnps.lineEdit_21.text()],
                                    "KEEPFILES":[self.ctopagnps.lineEdit_9.text()],"OPTIMIZE":[self.ctopagnps.lineEdit_12.text()],
                                    "MODULE":[self.ctopagnps.lineEdit_13.text()],"OUTPUT":[self.ctopagnps.lineEdit_16.text()],
                                    "READOUT":[self.ctopagnps.lineEdit_23.text()],"READPATH":[self.ctopagnps.lineEdit_24.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"TOPAGNPS.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select project folder", "Please before creating the topagnps control file first select de project folder you are going to work with",level=Qgis.Warning)
            return 
        self.ctopagnps.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_peg(self):
        #Función para que cuando se le de al botón de aceptar en el control file de peg se cree el control file PEG.csv con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
        control_file = pd.DataFrame(data = {"Input":[self.cpeg.lineEdit.text()],"CTI_value":[self.cpeg.lineEdit_2.text()],
                                    "Accum_pct":[self.cpeg.lineEdit_3.text()],"Display_Drainage_Option":[self.cpeg.lineEdit_4.text()],
                                    "Display_Location_Option":[self.cpeg.lineEdit_5.text()],"ASC_Path":[self.cpeg.lineEdit_6.text()],
                                    "CSV_Path":[self.cpeg.lineEdit_7.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"PEG.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the PEG control file first select de DEM you are going to use",level=Qgis.Warning)
            return 
        self.cpeg.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_agbuf(self):
        #Función para que cuando se le de al botón de aceptar en el control file de agbuf se cree el control file Agbuf.csv con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
        control_file = pd.DataFrame(data = {"BUFFER":[self.cagbuf.lineEdit.text()],"VEGETATION":[self.cagbuf.lineEdit_2.text()],
                                    "FOREST":[self.cagbuf.lineEdit_3.text()],"GRASS":[self.cagbuf.lineEdit_4.text()],
                                    "C_THRESHOLD":[self.cagbuf.lineEdit_5.text()],"R_THRESHOLD":[self.cagbuf.lineEdit_6.text()],
                                    "UNITS":[self.cagbuf.lineEdit_7.text()],"ASC_PATH":[self.cagbuf.lineEdit_8.text()],
                                    "CSV_PATH":[self.cagbuf.lineEdit_9.text()]})
        #If Forest keyword is not used, then delete the column
        if str(self.cagbuf.lineEdit_3.text())=="":control_file.drop("FOREST",axis = 1,inplace = True)
        
        try:
            control_file.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"AgBuf.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the AGBUF control file first select de DEM you are going to use",level=Qgis.Warning)
            return 
        self.cagbuf.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_agwet(self):
        #Función para que cuando se le de al botón de aceptar en el control file de agwet se cree el control file Agwet.csv con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
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
            control_file.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"AgWet.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the AGWET control file first select de DEM you are going to use",level=Qgis.Warning)
            return 
        self.cagwet.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_concepts(self):
        #Función para que cuando se le de al botón de aceptar en el control file de concepts se cree el control file CONCEPTS.csv con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
        control_file = pd.DataFrame(data = {"UPSTREAM_REACH_ID":[self.cconcepts.lineEdit.text()],"DOWNSTREAM_REACH_ID":[self.cconcepts.lineEdit_2.text()],"ASC_Path":[self.cconcepts.lineEdit_3.text()],"CSV_Path":[self.cconcepts.lineEdit_4.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"CONCEPTS.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the CONCEPTS control file first select de DEM you are going to use",level=Qgis.Warning)
            return 
        self.cconcepts.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_pothole(self):
        #Función para que cuando se le de al botón de aceptar en el control file de pothole se cree el control file POTHOLE.csv con los datos que se han puesto
        control_file = pd.DataFrame(data = {"POTHOLE_OPTION":[self.cpothole.lineEdit.text()],"POTHOLE_SURFACE_AREA":[self.cpothole.lineEdit_2.text()],
                                            "ASC_Path":[self.cpothole.lineEdit_3.text()],"CSV_Path":[self.cpothole.lineEdit_4.text()]})
        try:
            control_file.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"POTHOLE.csv", index=False, float_format='%.5f')
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the POTHOLE control file first select de DEM you are going to use",level=Qgis.Warning)
            return 
        self.cpothole.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_rasfor(self):
        #Función para que cuando se le de al botón de aceptar en el control file de rasfor se cree el control file rasfor.inp con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
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
            iface.messageBar().pushMessage("Select Output Format Option", "please choose among the four output format options",level=Qgis.Warning)
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
            f = open(self.direccion+"\\"+"Preprocessing_inputs\\"+"rasfor.inp","w+")
        except:
            iface.messageBar().pushMessage("Select Project Folder", "Please before creating the RASFOR data first select de project folder you are going to use",level=Qgis.Warning)
            return 
        f.write(texto_nuevo)
        f.close()
        self.crasfor.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_raspro(self):
        #Función para que cuando se le de al botón de aceptar en el control file de raspro se cree el control file raspro.inp con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
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
            f = open(self.direccion+"\\"+"Preprocessing_inputs\\"+"raspro.inp","w+")
        except:
            iface.messageBar().pushMessage("Select Project Folder", "Please before creating the RASPRO data first select de project folder you are going to use",level=Qgis.Warning)
            return 
        f.write(texto_nuevo)
        f.close()
        self.craspro.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def create_control_file_dednm(self):
        #Función para que cuando se le de al botón de aceptar en el control file de dednm se cree el control file dednm.inp con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
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
            iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning)
            return 
        #Se obteiene el texto de un archivo rasfor (un ejemplo) para luego añadirle los valores que se han escogido en el plugin
        fichero = open(self.plugin_dir+"\Documentos\dednm.inp","r+")
        texto = fichero.read()
        fichero.close()
        #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
        try:
            lista_parametros = [utm_zone,utm_e,utm_n,dem_r,dem_c,min_e,max_e,indet_el,dem_res,dem_or,out_row,out_col,dem_proc,dem_smooth,passes,center,cross,diagonal,perform_raster,partial,csa,mscl,depression,cal_options,progr_rep,inp_data,drainage_area,subcatchment_area,subcatchment_window]
        except:
            iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning)
            return 
        lista = [1101, 1377, 1657, 1871, 2088, 2249, 2411, 2765, 2879, 3258, 3632, 4012, 4480, 4817, 5096, 5346, 5830, 5834, 5838, 6202, 6740, 7506, 10873, 11034, 11419, 11498, 11568, 11639, 11714]
        texto_nuevo = texto
        contador = 0
        for i in range(len(lista_parametros)):
            texto_nuevo = texto_nuevo[0:lista[i]+contador]+str(lista_parametros[i])+texto_nuevo[lista[i]+contador+1:]
            contador += len(str(lista_parametros[i]))-1
        try:
            f = open(self.direccion+"\\"+"Preprocessing_inputs\\"+"dednm.inp","w+")
        except:
            iface.messageBar().pushMessage("Select DEM", "Please before creating the DEDNM data first select de DEM you are going to use",level=Qgis.Warning)
            return 
        f.write(texto_nuevo)
        f.close()
        self.dednm.close()
        #Update use of control files
        self.show_existing_control_files()
    
    def create_control_file_agflow(self,control_type):
        #Función para que cuando se le de al botón de aceptar en el control file de agflow se cree el control file dednm.inp con los datos que se han puesto
        #Si no existe la carpeta de preprocessing inputs entonces se crea
        self.create_preprocessing_inputs_folder()
        #Función para pasar de 1 a T y de 0 a F
        def funcion_t(numero):
            if numero==1:
                return "T"
            elif numero ==0:
                return "F"
        #Inputs
        #Create inp
        if control_type=="inp":
            #Se obtiene el texto de un archivo rasfor (un ejemplo) para luego añadirle los valores que se han escogido en el plugin
            fichero = open(self.plugin_dir+r"\Documentos\agflow.inp","r+")
            texto = fichero.read()
            fichero.close()
            #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
            try:
                if self.agflow.lineEdit_4.text() =="":slope="1"
                else:slope= str(int(self.agflow.lineEdit_4.text()))

                if self.agflow.lineEdit_5.text()=="":maxim_d="0.99"
                else:maxim_d=float(self.agflow.lineEdit_5.text())

                if self.agflow.lineEdit_6.text()=="":maxim_pl="300.0"
                else:maxim_pl=float(self.agflow.lineEdit_6.text())

                if self.agflow.lineEdit_7.text()=="":maxim_ps="100.0"
                else:maxim_ps=float(self.agflow.lineEdit_7.text())
                
                use=funcion_t(int(self.agflow.checkBox.isChecked()))
                write=funcion_t(int(self.agflow.checkBox_2.isChecked()))
                arc=funcion_t(int(self.agflow.checkBox_3.isChecked()))
                dat=funcion_t(int(self.agflow.checkBox_4.isChecked()))
                use_file=funcion_t(int(self.agflow.checkBox_5.isChecked()))
            
            except:
                iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning,duration = 10)
                return
            
            texto_nuevo = texto.replace("aaaaa",f"    {slope}     {maxim_d}     {maxim_pl}     {maxim_ps}     {use}     {write}     {arc}     {dat}     {use_file}")
            try:
                f = open(self.direccion+"\\"+"Preprocessing_inputs\\"+"AGFCNT.inp","w+")
            except:
                iface.messageBar().pushMessage("Select project folder", "Please before creating the agflow data first select de project folder you are going to use",level=Qgis.Warning)
                return 
            f.write(texto_nuevo)
            f.close()
        #Create csv
        if control_type=="csv":
            reas=int(self.agflow.checkBox_6.isChecked())
            path = str(self.agflow.lineEdit_8.text())
            df = pd.DataFrame(data = {"REASSIGN":[reas],"ASC_PATH":[path]})
            df.to_csv(self.direccion+"\\"+"Preprocessing_inputs\\"+"AGFLOW.csv", index=False, float_format='%.5f')
            
        self.agflow.close()
        #Update use of control files
        self.show_existing_control_files()
        
    def asignar_valores_control_dialogo(self):
        #Añadir los valores del control file al plugin
        #Primero el error para de si no se ha seleccionado la carpeta del proyecto y por lo tanto no existe self.direccion
        if hasattr(self,"direccion"):
            pass
        else:
            iface.messageBar().pushMessage("Select the project folder", "To view the parameters of the control files and to modify them, first select the project folder",level=Qgis.Warning,duration = 10)
            return 
        #TOPAGNPS
        #Primero se borra lo que haya previamente
        dialogos = [self.ctopagnps.lineEdit_7,self.ctopagnps.lineEdit_8,self.ctopagnps.lineEdit_5,self.ctopagnps.lineEdit_14,self.ctopagnps.lineEdit_3,self.ctopagnps.lineEdit_10,self.ctopagnps.lineEdit_19,self.ctopagnps.lineEdit_20,self.ctopagnps.lineEdit_18,self.ctopagnps.lineEdit_2,self.ctopagnps.lineEdit,self.ctopagnps.lineEdit_11,self.ctopagnps.lineEdit_17,self.ctopagnps.lineEdit_6,self.ctopagnps.lineEdit_4,self.ctopagnps.lineEdit_21,self.ctopagnps.lineEdit_9,self.ctopagnps.lineEdit_12,self.ctopagnps.lineEdit_15,self.ctopagnps.lineEdit_22,self.ctopagnps.lineEdit_13,self.ctopagnps.lineEdit_16,self.ctopagnps.lineEdit_23,self.ctopagnps.lineEdit_24]
        for i in dialogos:
            i.setText("")
        #Luego se pone lo que hay en el control file
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\TOPAGNPS.csv"):
            control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"TOPAGNPS.csv",encoding = "ISO-8859-1",delimiter=",")
            columnas = ["FILENAME","FORMAT","DEMPROC","OUTFORMAT","CSA","MSCL","UTME","UTMN","ROWS","COLS","CELLSIZE","NODATA","OUTSNAP","DNMCNT","DEMEDGE","VERBOSE","KEEPFILES","OPTIMIZE","OUTCOL","OUTROW","MODULE","OUTPUT","READOUT","READPATH"]
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
        #Primero se borra lo que haya previamente
        dialogos = [self.cpeg.lineEdit,self.cpeg.lineEdit_2,self.cpeg.lineEdit_3]
        for i in dialogos:
            i.setText("")
        #Luego se pone lo que hay en el control file
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\PEG.csv"):
            control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"PEG.csv",encoding = "ISO-8859-1",delimiter=",")
            columnas =["Input","CTI_value","Accum_pct"]
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
        #Primero se borra lo que haya previamente
        dialogos = [self.cagbuf.lineEdit,self.cagbuf.lineEdit_2,self.cagbuf.lineEdit_3,self.cagbuf.lineEdit_4,self.cagbuf.lineEdit_5,self.cagbuf.lineEdit_6,self.cagbuf.lineEdit_7,self.cagbuf.lineEdit_8,self.cagbuf.lineEdit_9]
        for i in dialogos:
            i.setText("")
        #Luego se pone lo que hay en el control file
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AgBuf.csv"):
            control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"AgBuf.csv",encoding = "ISO-8859-1",delimiter=",")
            columnas =["BUFFER","VEGETATION","FOREST","GRASS","C_THRESHOLD","R_THRESHOLD","UNITS","ASC_PATH","CSV_PATH"]
            for i in range(len(columnas)):
                try:
                    if str(control_file[columnas[i]].iloc[0]) == "nan":
                        texto = ""
                    else:
                        texto = str(control_file[columnas[i]].iloc[0])
                    dialogos[i].setText(texto)
                except:
                    pass
        
        #AgFlow
        #First we delete the previous
        self.agflow.lineEdit_4.setText("")
        self.agflow.lineEdit_5.setText("")
        self.agflow.lineEdit_6.setText("")
        self.agflow.lineEdit_7.setText("")
        self.agflow.checkBox.setChecked(False)
        self.agflow.checkBox_2.setChecked(False)
        self.agflow.checkBox_3.setChecked(False)
        self.agflow.checkBox_4.setChecked(False)
        self.agflow.checkBox_5.setChecked(False)
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AGFCNT.inp"):
            try:
                #After we put the control files data
                fichero = open(self.direccion+"\\Preprocessing_inputs"+"\AGFCNT.inp","r+")
                texto = fichero.read()
                fichero.close()
                def from_string_to_condition(string):
                    if string == "F":
                        return False
                    elif string =="F\n":
                        return False
                    else:
                        return True
                        
                valores = texto[237:].split("     ")
                self.agflow.lineEdit_4.setText(valores[0])
                self.agflow.lineEdit_5.setText(valores[1])
                self.agflow.lineEdit_6.setText(valores[2])
                if valores[3]=="100.0":
                    self.agflow.lineEdit_7.setText("")
                else:
                    self.agflow.lineEdit_7.setText(valores[3])
                self.agflow.checkBox.setChecked(from_string_to_condition(valores[4]))
                self.agflow.checkBox_2.setChecked(from_string_to_condition(valores[5]))
                self.agflow.checkBox_3.setChecked(from_string_to_condition(valores[6]))
                self.agflow.checkBox_4.setChecked(from_string_to_condition(valores[7]))
                self.agflow.checkBox_5.setChecked(from_string_to_condition(valores[8]))
            except:
                pass
                
        #First we delete the previous
        self.agflow.checkBox_6.setChecked(False)
        self.agflow.lineEdit_8.setText("")
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AGFLOW.csv"):
            try:
                #After we put the control files data
                control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"AGFLOW.csv",encoding = "ISO-8859-1",delimiter=",")
                if control_file["REASSIGN"].iloc[0]==0 or control_file["REASSIGN"].iloc[0]=="":
                    self.agflow.checkBox_6.setChecked(False)
                else:
                    self.agflow.checkBox_6.setChecked(True)
                if type(control_file["ASC_PATH"].iloc[0])!=str:
                    self.agflow.lineEdit_8.setText("")
                else:
                    self.agflow.lineEdit_8.setText(control_file["ASC_PATH"].iloc[0])
            except:
                pass
        
        #AGWET
        #Primero se borra lo que haya previamente
        dialogos = [self.cagwet.lineEdit,self.cagwet.lineEdit_18,self.cagwet.lineEdit_17,self.cagwet.lineEdit_11,self.cagwet.lineEdit_12,self.cagwet.lineEdit_14,self.cagwet.lineEdit_21,self.cagwet.lineEdit_20,self.cagwet.lineEdit_8,self.cagwet.lineEdit_9,self.cagwet.lineEdit_7,self.cagwet.lineEdit_13,self.cagwet.lineEdit_10,self.cagwet.lineEdit_15,self.cagwet.lineEdit_19,self.cagwet.lineEdit_2,self.cagwet.lineEdit_3,self.cagwet.lineEdit_4,self.cagwet.lineEdit_5,self.cagwet.lineEdit_6]
        for i in dialogos:
            i.setText("")
        #Luego se pone lo que hay en el control file
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\AgWet.csv"):
            control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"AgWet.csv",encoding = "ISO-8859-1",delimiter=",")
            columnas =["FILENAME","BREACH_BARRIER","BARRIER_HEIGHT_OPTION","BARRIER_HEIGHT","BARRIER_HEIGHT_INCREMENT","BARRIER_HEIGHT_MAX","WETLAND_ID_OPTION","EROSION_INDEX_OPTION","EROSION_INDEX_THRESHOLD","DA_THRESHOLD","WI_THRESHOLD","MIN_WETLAND_RATIO","MAX_WETLAND_RATIO","BUFFER_WIDTH","BUFFER_EXTENT_OPTION","BUFFER_IDS_FILENAME","BUFFER_VEG_FILENAME","BUFFER_ZONE_FILENAME","ASC_PATH","CSV_PATH"]
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
        #Primero se borra lo que haya previamente
        dialogos = [self.cconcepts.lineEdit,self.cconcepts.lineEdit_2]
        for i in dialogos:
            i.setText("")
        #Luego se pone lo que hay en el control file
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\CONCEPTS.csv"):
            control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"CONCEPTS.csv",encoding = "ISO-8859-1",delimiter=",")
            columnas =["UPSTREAM_REACH_ID","DOWNSTREAM_REACH_ID"]
            
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
        #Primero se borra lo que haya previamente
        dialogos = [self.cpothole.lineEdit,self.cpothole.lineEdit_2,self.cpothole.lineEdit_3,self.cpothole.lineEdit_4]
        for i in dialogos:
            i.setText("")
        #Luego se pone lo que hay en el control file
        if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\POTHOLE.csv"):
            control_file = pd.read_csv(self.direccion+"\\Preprocessing_inputs"+"\\"+"POTHOLE.csv",encoding = "ISO-8859-1",delimiter=",")
            columnas =["POTHOLE_OPTION","POTHOLE_SURFACE_AREA","ASC_Path","CSV_Path"]
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
        self.output.raise_()
        self.output.activateWindow()
    
    def output_topagnps(self,output_type):
        #Método para mostrar los outputs de TopAGNPS
        #Se pone el epsg del proyecto
        self.epsg = QgsProject.instance().crs().authid()
        #Primero se pone condición para que se haya elegido el DEM
        if self.output.lineEdit_2.text()=="":
            iface.messageBar().pushMessage("Select the project folder", "To view the parameters of the control files and to modify them, first select the project folder",level=Qgis.Warning)
            return
        #Se pone una función para cambiar coordenadas y otra para la dirección de ficheros que será usada luego por varios
        def change_coordinates(filename,outputname):
            input_raster = gdal.Open(fichero(filename))
            output_raster = fichero(outputname)
            warp = gdal.Warp(output_raster,input_raster,dstSRS=self.epsg)
            warp = None # Closes the files
        def fichero(nombre):
            return self.output.lineEdit_2.text()+"\\"+nombre
        
        def save_vectorials(name):
            #Funcion para guardar las capas vectoriales en otra carpeta
            #Se crea carpeta
            directory = "Vectorial_outputs"
            parent_dir = self.output.lineEdit_2.text()
            path_file = os.path.join(parent_dir, directory)
            mode = 0o666
            try:
                os.mkdir(path_file, mode)
            except:
                pass
            #Si existe el archivo entonces se guarda en otro nuevo
            if os.path.exists(parent_dir+"//"+directory+"//"+f"{name}.gpkg"):
                contador = 0
                while True:
                    if not os.path.exists(parent_dir+"//"+directory+"//"+f"{name}_{contador}.gpkg"):
                        direction = parent_dir+"//"+directory+"//"+f"{name}_{contador}.gpkg"
                        break
                    contador +=1
            else:
                direction = parent_dir+"//"+directory+"//"+f"{name}.gpkg"
            return direction
            
     
        #CELDAS RASTER
        if output_type == "Cell_raster":
            if not os.path.exists(fichero("AnnAGNPS_Cell_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Cell_IDs.asc does not exist",level=Qgis.Warning)
                return 
            change_coordinates("AnnAGNPS_Cell_IDs.asc","AnnAGNPS_Cell_IDs_EPSG.asc")
            layer = QgsRasterLayer(fichero("AnnAGNPS_Cell_IDs_EPSG.asc"),"Cells_ras")
            QgsProject.instance().addMapLayer(layer)
                
        #CELDAS VECTORIAL
        elif output_type == "Cell_vectorial":
            if not os.path.exists(fichero("AnnAGNPS_Cell_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Cell_IDs.asc does not exist",level=Qgis.Warning)
                return
            direccion = save_vectorials("cell")
            change_coordinates("AnnAGNPS_Cell_IDs.asc","cell_1.asc")
            processing.run("grass7:r.to.vect", {'input':fichero("cell_1.asc"),
                'type':2,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':direccion,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(direccion,"Cells_vec")
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
                iface.messageBar().pushMessage("Output not found", "BOUND.ASC does not exist",level=Qgis.Warning)
                return
            change_coordinates("BOUND.ASC","BOUND_EPSG.ASC")
            layer = QgsRasterLayer(fichero("BOUND_EPSG.ASC"),"Watershed_boundary_ras")
            QgsProject.instance().addMapLayer(layer)
            
        #DELIMITACIÓN DE LA CUENCA VECTORIAL
        elif output_type == "Boundary_vectorial":
            if not os.path.exists(fichero("BOUND.ASC")):
                iface.messageBar().pushMessage("Output not found", "BOUND.ASC does not exist",level=Qgis.Warning)
                return
            direccion = save_vectorials("bound")
            change_coordinates("BOUND.ASC","BOUND_EPSG.ASC")
            processing.run("grass7:r.to.vect", {'input':fichero("BOUND_EPSG.ASC"),
                'type':2,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':direccion,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(direccion,"Watershed_boundary_vec")
            QgsProject.instance().addMapLayer(layer)
            
        #REACHES RASTER
        elif output_type == "Reaches_raster":
            if not os.path.exists(fichero("AnnAGNPS_Reach_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Reach_IDs.asc does not exist",level=Qgis.Warning)
                return
            change_coordinates("AnnAGNPS_Reach_IDs.asc","AnnAGNPS_Reach_IDs_EPSG.asc")
            layer = QgsRasterLayer(fichero("AnnAGNPS_Reach_IDs_EPSG.asc"),"Reaches_ras")
            QgsProject.instance().addMapLayer(layer)
        
        #REACHES VECTORIAL
        elif output_type == "Reaches_vectorial":
            if not os.path.exists(fichero("AnnAGNPS_Reach_IDs.asc")):
                iface.messageBar().pushMessage("Output not found", "AnnAGNPS_Reach_IDs.asc does not exist",level=Qgis.Warning)
                return
            change_coordinates("AnnAGNPS_Reach_IDs.asc","AnnAGNPS_Reach_IDs_EPSG.asc")
            direccion = save_vectorials("reaches")
            processing.run("grass7:r.to.vect", {'input':fichero("AnnAGNPS_Reach_IDs_EPSG.asc"),
                'type':0,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':direccion,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(direccion,"Reaches_vec")
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
                iface.messageBar().pushMessage("Output not found", "UPAREA.asc does not exist",level=Qgis.Warning)
                return
            layer = QgsRasterLayer(fichero("UPAREA.asc"),"Accumulated_area")
            QgsProject.instance().addMapLayer(layer)
        
        #TERRAIN SLOPE
        elif output_type == "Terrain_slope":
            if not os.path.exists(fichero("TSLOPE.ASC")):
                iface.messageBar().pushMessage("Output not found", "TSLOPE.ASC does not exist",level=Qgis.Warning)
                return
            layer = QgsRasterLayer(fichero("TSLOPE.ASC"),"Terrain_slope")
            QgsProject.instance().addMapLayer(layer)
        
        #HYDRAULIC SLOPE
        elif output_type == "Hydraulic":
            if not os.path.exists(fichero("HSLOPE.ASC")):
                iface.messageBar().pushMessage("Output not found", "HSLOPE.ASC does not exist",level=Qgis.Warning)
                return
            layer = QgsRasterLayer(fichero("HSLOPE.ASC"),"Hydraulic_slope")
            QgsProject.instance().addMapLayer(layer)

        #TERRAIN ASPECT
        elif output_type == "Terrain_aspect":
            if not os.path.exists(fichero("TASPEC.ASC")):
                iface.messageBar().pushMessage("Output not found", "TASPEC.ASC does not exist",level=Qgis.Warning)
                return
            layer = QgsRasterLayer(fichero("TASPEC.ASC"),"Terrain_aspect")
            QgsProject.instance().addMapLayer(layer)
        
        #RUSLE LS FACTOR
        elif output_type == "RUSLE":
            if not os.path.exists(fichero("AgFlow_LS_Factor.asc")):
                iface.messageBar().pushMessage("Output not found", "AgFlow_LS_Factor.asc does not exist",level=Qgis.Warning)
                return
            layer = QgsRasterLayer(fichero("AgFlow_LS_Factor.asc"),"RUSLE_LS_factor")
            QgsProject.instance().addMapLayer(layer)
        
        #CELL LONGEST FLOW PATH RASTER
        elif output_type == "Longest_raster":
            if not os.path.exists(fichero("AgFlow_Cell_Longest_Flow_Path.asc")):
                iface.messageBar().pushMessage("Output not found", "AgFlow_Cell_Longest_Flow_Path.asc does not exist",level=Qgis.Warning)
                return
            layer = QgsRasterLayer(fichero("AgFlow_Cell_Longest_Flow_Path.asc"),"Cell_longest_flow_raster")
            QgsProject.instance().addMapLayer(layer)

        #CELL LONGEST FLOW PATH VECTORIAL
        elif output_type == "Longest_vectorial":
            if not os.path.exists(fichero("AgFlow_Cell_Longest_Flow_Path.asc")):
                iface.messageBar().pushMessage("Output not found", "AgFlow_Cell_Longest_Flow_Path.asc does not exist",level=Qgis.Warning)
                return
            direccion = save_vectorials("longpath")
            change_coordinates("AgFlow_Cell_Longest_Flow_Path.asc","AgFlow_Cell_Longest_Flow_Path_epsg.asc")
            processing.run("grass7:r.to.vect", {'input':fichero("AgFlow_Cell_Longest_Flow_Path_epsg.asc"),
                'type':0,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':direccion,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})
            layer = QgsVectorLayer(direccion,"Cell_longest_flow_raster_vec")
            QgsProject.instance().addMapLayer(layer)
            #Cambio de formato de la capa
            symbol = QgsLineSymbol()
            symbol.setWidth(1)
            symbol.setColor(QColor.fromRgb(255, 0, 0))
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            layer.triggerRepaint()
            
        #PEG points
        elif output_type == "PEG_points":
            try:
                #Se importa el fichero donde se tienen las coordenadas de los puntos PEG
                fichero_summary = fichero("PEG_Summary.txt")
                summary = pd.read_csv(fichero_summary,encoding = "ISO-8859-1",delimiter=",")
                #Función para crear la capa con los puntos PEG
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg), "PEG_Points", "memory")
                    layer.dataProvider().addAttributes([QgsField("id", QVariant.String), 
                                                        QgsField("Drainage_area", QVariant.Double),
                                                        QgsField("Luparea", QVariant.Double),
                                                        QgsField("Subarea", QVariant.Double),
                                                        QgsField("Slope", QVariant.Double),
                                                        QgsField("CTI", QVariant.Double),
                                                        QgsField("Headcut_barrier", QVariant.Double),
                                                        QgsField("Stream_order", QVariant.Double),
                                                        QgsField("Cell_ID", QVariant.Double),
                                                        QgsField("Reach_ID", QVariant.Double),
                                                        QgsField("StreamCNT", QVariant.Double)])
                    layer.updateFields()
                    features = []
                    for i in range(len(summary)):
                        feature = QgsFeature()
                        feature.setFields(layer.fields())
                        x = summary.X.iloc[i]
                        y = summary.Y.iloc[i]
                        pt = QgsPointXY(x, y)
                        geom = QgsGeometry.fromPointXY(pt)
                        feature.setGeometry(geom)
                        feature.setAttribute("id", summary['GULLY_ID'].iloc[i])
                        feature.setAttribute("Drainage_area", float(summary.UPAREA.iloc[i]))
                        feature.setAttribute("Luparea", float(summary.LUPAREA.iloc[i]))
                        feature.setAttribute("Subarea", float(summary.SUBAREA.iloc[i]))
                        feature.setAttribute("Slope", float(summary.SLOPE.iloc[i]))
                        feature.setAttribute("CTI", float(summary.CTINDEX.iloc[i]))
                        feature.setAttribute("Headcut_barrier", float(summary.HCUT_B.iloc[i]))
                        feature.setAttribute("Stream_order", float(summary.STREAM_ORDER.iloc[i]))
                        feature.setAttribute("Cell_ID", float(summary.CELL_ID.iloc[i]))
                        feature.setAttribute("Reach_ID", float(summary.REACH_ID.iloc[i]))
                        feature.setAttribute("StreamCNT", float(summary.STREAMCNT.iloc[i]))
                        features.append(feature)
                    layer.dataProvider().addFeatures(features)
                    return layer
                summary_layer = create_layer()
                QgsProject.instance().addMapLayer(summary_layer)
            except:
                pass

    def files_directory(self):
        #Método para añadir la dirección de la carpeta del mdt a la interfaz de los inputs de AnnAGNPS
        lista = [self.inputs.l_1,self.inputs.l_23,self.inputs.l_47,self.inputs.l_53]
        for i in lista:
            if i.text()=="":
                i.setText(str(self.dlg.project.text()))
        
    def add_master(self):
        #Método para añadir la información de un archivo master a los inputs de AnnAGNPS
        #Se abre la opción de escoger archivo y se obtiene la información
        try:
            fname = QFileDialog.getOpenFileName(self.inputs,"Select master file",self.direccion+"\\Processing_inputs","CSV files (*.csv)")
        except:
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
            try:
                self.inputs.l_1.setText(statistics.mode([os.path.split(x)[0] for x in dic_watershed.values()]))
                self.inputs.l_23.setText(statistics.mode([os.path.split(x)[0] for x in dic_general.values()]))
                self.inputs.l_47.setText(statistics.mode([os.path.split(x)[0] for x in dic_climate.values()]))
                self.inputs.l_53.setText(statistics.mode([os.path.split(x)[0] for x in dic_simulation.values()]))
            except:
                pass
            
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
        
            #Uncheck TopAGNPS provided
            lista = [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3,self.inputs.checkBox_4,self.inputs.checkBox_5]
            for i in lista:
                i.setChecked(False)
        
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
            for i in [self.inputs.checkBox,self.inputs.checkBox_2,self.inputs.checkBox_3,self.inputs.checkBox_5]:
                i.setChecked(False)
        if section=="general":
            self.inputs.checkBox_4.setChecked(False)
        
    def change_directory_input(self,section):
        #Método para cambiar el directorio de las secciones en el diálog de AnnAGNPS input editor
        if section =="watershed":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.direccion)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_1.setText(fname)
        if section =="general":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.direccion)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_23.setText(fname)
        if section =="climate":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.direccion)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_47.setText(fname)
        if section =="simulation":
            if hasattr(self, 'mdt_directory'):
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", self.direccion)
            else:
                fname = QFileDialog.getExistingDirectory(self.inputs, "Select folder", "C/")
            if fname!="":
                self.inputs.l_53.setText(fname)
    
    def information_in_folder(self,carpeta):
        """Method to check if a folder has information about a QAnnAGNPS project"""
        carpetas_control = {
            "Preprocessing_inputs", 
            "Preprocessing_output", 
            "Processing_inputs", 
            "Processing_outputs"
        }
        if not carpeta.exists():
            return False
        # Listamos solo los nombres de lo que hay dentro de la subcarpeta
        contenido = {f.name for f in carpeta.iterdir() if f.is_dir()}
        # Si hay intersección entre los conjuntos, es válida
        return not contenido.isdisjoint(carpetas_control)
    
    
    def obtain_last_modified_folder(self):
        """Method to obtain the latest modified folder"""
        # Carpetas que sirven como "marca" de que es una carpeta de ejecución válida
        carpetas_control = {
            "Preprocessing_inputs", 
            "Preprocessing_output", 
            "Processing_inputs", 
            "Processing_outputs"
        }
        
        ruta_padre = Path(self.dlg.project.text())
        
        try:
            # 1. Buscamos todas las subcarpetas
            todas_las_subcarpetas = [d for d in ruta_padre.iterdir() if d.is_dir()]
            
            # 2. Filtramos solo las que cumplen tu condición técnica
            carpetas_validas = [d for d in todas_las_subcarpetas if self.information_in_folder(d)]
        
            if carpetas_validas:
                # 3. De las válidas, obtenemos la última modificada
                ultima_carpeta = max(carpetas_validas, key=lambda f: f.stat().st_mtime)
                
                return ultima_carpeta.name
                
            else:
                self.warning_message("No folders with the needed information where obtained")
        
        except:
            return
    
    def save_project(self,overwrite = False):
        #Método para guardar el proyecto
        
        #Si no existe una carepta de trabajo entonces error
        if not hasattr(self, "direccion"):
            self.warning_message("Please, select a working directory before saving the project")
            return
        
        #Si no se ha puesto nombre al proyecto entonces error
        name_of_project = self.dlg.name_of_project.text()
        if name_of_project =="":
            self.warning_message("Please select a name for the project before saving")
            return
        
        
        #Si el usuario hace una ejecucion con un nombre de proyecto y luego escoge otro nombre porque quiere que se guarde con otro nombre, entonces el nuevo nombre no tendrá una carpeta. Habrá que coger la información de la última carpeta que se ha modificado
        #Check if the name was selected has information
        if not self.information_in_folder(Path(self.direccion)):
            name_of_folder = self.obtain_last_modified_folder()
        else:
            name_of_folder = name_of_project
        
        #Create folder where the data of the proyect is going to be saved
        Path(self.carpeta_guardar_proyectos).mkdir(parents=True, exist_ok=True)
        
        
        #But if a project with the previous name has been saved previously then put a warning because there can be only one project with the same name
        existing_names = [nombre for nombre in os.listdir(self.carpeta_guardar_proyectos) if os.path.isdir(os.path.join(self.carpeta_guardar_proyectos, nombre))]
        
        if name_of_project in existing_names and not overwrite:
            #Open window to overwrite or not
            self.dlg_overwrite_project.show()
            self.dlg_overwrite_project.raise_()
            self.dlg_overwrite_project.activateWindow()
            return 
        
        #Create the folder of the project if it doesn't exist
        Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}").mkdir(parents=True, exist_ok=True)
        

        #Se obtienen los datos de los inputs
        #En el csv se van a guardar con la direccion haciendo referencia a la carpeta en donde se van a guardar
        def cambiar_carpeta_base(ruta_original, nueva_carpeta):
            p = Path(ruta_original)
            nueva_ruta = Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\{nueva_carpeta}") / p.name    
            return str(nueva_ruta)
    
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        if self.dlg.comboBox.currentIndex()>0:
            dem_layer = cambiar_carpeta_base(layers[self.dlg.comboBox.currentIndex() - 1].layer().dataProvider().dataSourceUri(),"Preprocessing_inputs")
            dem_name = layers[self.dlg.comboBox.currentIndex() - 1].layer().name()
        else:
            dem_layer = ""
            dem_name =""
        if self.dlg.cbSoil.currentIndex()>0:
            soil_layer = cambiar_carpeta_base(layers[self.dlg.cbSoil.currentIndex()-1].layer().dataProvider().dataSourceUri(),"Preprocessing_inputs")
            soil_name = layers[self.dlg.cbSoil.currentIndex()-1].layer().name()
            soil_column = [field.name() for field in layers[self.dlg.cbSoil.currentIndex()-1].layer().fields()][self.dlg.cbColumnSoil.currentIndex()]
        else:
            soil_layer = ""
            soil_name = ""
            soil_column = ""
        if self.dlg.cbMan.currentIndex()>0:
            use_layer = cambiar_carpeta_base(layers[self.dlg.cbMan.currentIndex()-1].layer().dataProvider().dataSourceUri(),"Preprocessing_inputs")
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
            buffer_layer = cambiar_carpeta_base(layers[self.dlg.comboBox_2.currentIndex()-1].layer().dataProvider().dataSourceUri(),"Preprocessing_inputs")
            buffer_name = layers[self.dlg.comboBox_2.currentIndex()-1].layer().name()
        else:
            buffer_layer = ""
            buffer_name = ""
        if self.dlg.comboBox_3.currentIndex()>0:
            vegetation_layer = cambiar_carpeta_base(layers[self.dlg.comboBox_3.currentIndex()-1].layer().dataProvider().dataSourceUri(),"Preprocessing_inputs")
            vegetation_name = layers[self.dlg.comboBox_3.currentIndex()-1].layer().name()
        else:
            vegetation_layer = ""
            vegetation_name = ""
        unique_soil = self.dlg.lineEdit.text()
        unique_landuse = self.dlg.lineEdit_2.text()
        # Se crea el diccionario en el que se asigna a cada entrada un valor
        dic_save = {"Input":"value","project_folder":str(self.dlg.project.text()),"epsg":QgsProject.instance().crs().authid(),"dem": dem_layer,"dem_name":dem_name,"soil_layer":soil_layer,"soil_name":soil_name,"soil_column":soil_column,"use_layer":use_layer,"use_name":use_name,"use_column":use_column,
            "buffer_layer":buffer_layer,"buffer_name":buffer_name,"vegetation_layer":vegetation_layer,"vegetation_name":vegetation_name,"unique_soil":unique_soil,"unique_landuse":unique_landuse,
            "add_outlet":self.dlg.checkBox_2.isChecked(),"execute_topagnps":self.dlg.cbTop.isChecked(),"execute_annagnps":self.dlg.cbAnn.isChecked()}
            
        
        dic_save_two = {"watershed_directory":cambiar_carpeta_base(self.inputs.l_1.text(),"Processing_inputs"),
            "general_directory":cambiar_carpeta_base(self.inputs.l_23.text(),"Processing_inputs"),"climate_directory":cambiar_carpeta_base(self.inputs.l_47.text(),"Processing_inputs"),
            "simulation_directory":cambiar_carpeta_base(self.inputs.l_53.text(),"Processing_inputs"),"cell_topagpns_provided":self.inputs.checkBox.isChecked(),"eg_topagpns_provided":self.inputs.checkBox_2.isChecked(),
            "reach_topagpns_provided":self.inputs.checkBox_3.isChecked(),"riparian_topagpns_provided":self.inputs.checkBox_4.isChecked(),"wetland_topagpns_provided":self.inputs.checkBox_5.isChecked()}
        
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


        #Union of dictionary
        dic_save = dic_save|dic_save_two|{k: v.text() for k, v in master_dict.items()}
        
    
        
        
        
        #Function to eliminate what is inside of a folder
        def delete_files_and_folders(folder):
            carpeta = Path(self.carpeta_guardar_proyectos+"\\"+folder)
            # Borra todo el contenido de la carpeta
            for item in carpeta.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()          
                    elif item.is_dir():
                        shutil.rmtree(item) 
                except:
                    pass
                    
        
        #Se elimina todo lo que había dentro de la carpeta
        delete_files_and_folders(name_of_project)
        
        # Se guarda el archivo CSV utilizando la API de QGIS
        file_path = self.carpeta_guardar_proyectos+f"\\{name_of_project}\\{name_of_project}.csv"
        try:
            with open(file_path, 'w') as file:
                for key, value in dic_save.items():
                    if key in master_dict and os.path.isabs(value):
                        value = Path(value).name
                        file.write(f"{key},{value}\n")
                    else:
                        file.write(f"{key},{value}\n")
        except:
            iface.messageBar().pushMessage("Error Saving Project", f"Please close {file_path}" ,level=Qgis.Warning)
            return
        
        
        #First we move the inputs of preprocessing
        if os.path.exists(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Preprocessing_inputs"):
            #Create folder
            Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Preprocessing_inputs").mkdir(parents=True, exist_ok=True)
            #We eliminate what is inside
            delete_files_and_folders(f"{name_of_project}\\"+"Preprocessing_inputs")
            
            #First move the files selected in the interface to self.direccion+"\\Preprocessing_inputs"
            self.create_folder_preprocessing_and_move_files()
            
            #Move all files
            
            for elemento in os.listdir(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Preprocessing_inputs"):
                try:
                    ruta_origen = os.path.join(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Preprocessing_inputs", elemento)
                    ruta_destino = os.path.join(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Preprocessing_inputs", elemento)

                    if os.path.isfile(ruta_origen):
                        # Copiar archivos
                        shutil.copy2(ruta_origen, ruta_destino)
                    elif os.path.isdir(ruta_origen):
                        # Copiar carpetas completas
                        shutil.copytree(ruta_origen, ruta_destino, dirs_exist_ok=True)
                except:
                    pass
            
        #Now the preprocessing outputs
        if os.path.exists(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Preprocessing_outputs"):
            #Create folder
            Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Preprocessing_outputs").mkdir(parents=True, exist_ok=True)
            #We eliminate what is inside
            delete_files_and_folders(f"{name_of_project}\\"+"Preprocessing_outputs")
            #Move all files
            for elemento in os.listdir(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Preprocessing_outputs"):
                try:
                    ruta_origen = os.path.join(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Preprocessing_outputs", elemento)
                    ruta_destino = os.path.join(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Preprocessing_outputs", elemento)

                    if os.path.isfile(ruta_origen):
                        # Copiar archivos
                        shutil.copy2(ruta_origen, ruta_destino)
                    elif os.path.isdir(ruta_origen):
                        # Copiar carpetas completas
                        shutil.copytree(ruta_origen, ruta_destino, dirs_exist_ok=True)
                except:
                    pass
        
        #Now Processing inputs
        if os.path.exists(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Processing_inputs"):
            #Create folder
            Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Processing_inputs").mkdir(parents=True, exist_ok=True)
            #We eliminate what is inside
            delete_files_and_folders(f"{name_of_project}\\"+"Processing_inputs")
            
            #First move the files selected in the interface to self.direccion+"\\Processing_inputs"
            self.direccion = self.dlg.project.text()+f"\\{name_of_folder}"
            self.create_folder_processing_and_move_files()
            self.direccion = self.dlg.project.text()+f"\\{name_of_project}"
            
            #Move all files
            for elemento in os.listdir(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Processing_inputs"):
                try:
                    ruta_origen = os.path.join(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Processing_inputs", elemento)
                    ruta_destino = os.path.join(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Processing_inputs", elemento)

                    if os.path.isfile(ruta_origen):
                        # Copiar archivos
                        shutil.copy2(ruta_origen, ruta_destino)
                    elif os.path.isdir(ruta_origen):
                        # Copiar carpetas completas
                        shutil.copytree(ruta_origen, ruta_destino, dirs_exist_ok=True)
                except:
                    pass
        
        #Processing outputs
        if os.path.exists(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Processing_outputs"):
            #Create folder
            Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Processing_outputs").mkdir(parents=True, exist_ok=True)
            #We eliminate what is inside
            delete_files_and_folders(f"{name_of_project}\\"+"Processing_outputs")
            #Move all files
            for elemento in os.listdir(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Processing_outputs"):
                try:
                    ruta_origen = os.path.join(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Processing_outputs", elemento)
                    ruta_destino = os.path.join(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Processing_outputs", elemento)

                    if os.path.isfile(ruta_origen):
                        # Copiar archivos
                        shutil.copy2(ruta_origen, ruta_destino)
                    elif os.path.isdir(ruta_origen):
                        # Copiar carpetas completas
                        shutil.copytree(ruta_origen, ruta_destino, dirs_exist_ok=True)
                        
                except:
                    pass
        
        
        #Sensitivity analysis
        if os.path.exists(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Sensitivity_analysis"):
            #Create folder
            Path(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Sensitivity_analysis").mkdir(parents=True, exist_ok=True)
            #We eliminate what is inside
            delete_files_and_folders(f"{name_of_project}\\"+"Sensitivity_analysis")
            #Move all files
            for elemento in os.listdir(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Sensitivity_analysis"):
                try:
                    ruta_origen = os.path.join(self.dlg.project.text()+f"\\{name_of_folder}"+"\\Sensitivity_analysis", elemento)
                    ruta_destino = os.path.join(self.carpeta_guardar_proyectos+f"\\{name_of_project}\\Sensitivity_analysis", elemento)

                    if os.path.isfile(ruta_origen):
                        # Copiar archivos
                        shutil.copy2(ruta_origen, ruta_destino)
                    elif os.path.isdir(ruta_origen):
                        # Copiar carpetas completas
                        shutil.copytree(ruta_origen, ruta_destino, dirs_exist_ok=True)
                        
                except:
                    pass
        
        #Update the available projects in the computer
        self.update_saved_projects()
        
        
    def load_project(self):
        #Método para cargar el proyecto
        
        #If there is not working directory selected then error
        if self.dlg.project.text()=="":
            self.warning_message("Please select a working directory where the files are going to be loaded")
            return
        
        #Se abre el archivo
        name_of_project = self.dlg.combo_created_projects.currentText()
        csv_file = self.carpeta_guardar_proyectos +"\\"+name_of_project+"\\"+name_of_project+".csv"
        
        project_df = pd.read_csv(csv_file,encoding = "ISO-8859-1",delimiter=",")

        #Se añade el epsg
        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(str(project_df[project_df.iloc[:,0]=="epsg"].iloc[0,1])))
        
        #Put the name to the project
        self.dlg.name_of_project.setText(name_of_project)
        
        #Move all the folders to the new folder
        origen = Path(self.carpeta_guardar_proyectos +"\\"+name_of_project)
        destino = Path(self.direccion)
        
        
        destino.mkdir(parents=True, exist_ok=True)
        for carpeta in origen.iterdir():
            if carpeta.is_dir():
                shutil.copytree(
                    carpeta,
                    destino / carpeta.name,
                    dirs_exist_ok=True
                )
        
        
        #Función para pasar de la ruta de la carpeta donde se guarda el proyecto a la carpeta de trabajo cargada
        def change_direction(ruta):
            try:
                ruta_nueva = Path(ruta).parts[-2:]
                resultado = str(Path(*ruta_nueva))
                return self.direccion + "\\"+resultado
            except:
                return "nan"
            
        
        #Primero se comprueba que existen las capas que estaban en el proyecto guardado. Si no lo están, se añaden. 
        layers = {"dem":change_direction(project_df[project_df.iloc[:,0]=="dem"].iloc[0,1]),"soil":change_direction(project_df[project_df.iloc[:,0]=="soil_layer"].iloc[0,1]),
            "use":change_direction(project_df[project_df.iloc[:,0]=="use_layer"].iloc[0,1]),"buffer":change_direction(project_df[project_df.iloc[:,0]=="buffer_layer"].iloc[0,1]),
            "vegetation":change_direction(project_df[project_df.iloc[:,0]=="vegetation_layer"].iloc[0,1])}
        #Bucle para añadir capas
        names = {"dem":"dem_name","buffer":"buffer_name","vegetation":"vegetation_name"}
        for i in layers.keys():
            layer_exists = False
            for layer in QgsProject.instance().mapLayers().values():
                if not layers[i]=="nan" and os.path.abspath(layer.source()) == os.path.abspath(layers[i]):
                    layer_exists = True
                    break
            if not layer_exists:
                if (i == "dem" or i == "buffer" or i == "vegetation" ) and not layers[i]=="nan":
                    layer = QgsRasterLayer(layers[i],project_df[project_df.iloc[:,0]==names[i]].iloc[0,1])
                    QgsProject.instance().addMapLayer(layer)
                elif not layers[i]=="nan":
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
        all_layers = QgsProject.instance().layerTreeRoot().children()
        l = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
        combo_lista = [layer.name() for layer in l]
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
        
        #poner los control files
        
        #Se añaden las capas a los combobox
        all_layers = QgsProject.instance().layerTreeRoot().children()
        layers_l = [node for node in all_layers if isinstance(node, QgsLayerTreeLayer)]
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
            self.inputs.checkBox_5.setChecked(retrieve_data("wetland_topagpns_provided"))
        except:
            self.warning_message("Error Loading Project\nThe file you have selected does not have the format or information necessary to upload a project")
            return 
            
        
        #Inputs de AnnAGNPS
        load_dict = {"watershed_directory":self.inputs.l_1,"general_directory":self.inputs.l_23,"climate_directory":self.inputs.l_47,
                    "simulation_directory":self.inputs.l_53}
        for i in load_dict.keys():
            try:
                load_dict[i].setText(change_direction(str(project_df[project_df.iloc[:,0]==i].iloc[0,1])))
            except:
                self.warning_message("Error Loading Project\nThe file you have selected does not have the format or information necessary to upload a project")
                return 
        
                    
                    
        load_dict = {"AnnAGNPS ID":self.inputs.l_54,
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
                self.warning_message("Error Loading Project\nThe file you have selected does not have the format or information necessary to upload a project")
                return 
            
        
        
    def update_saved_projects(self,update_scenario = True):
        """Method to update the projects that are available in the computer"""
        #In the main windo. 
        project_names = [
            f for f in os.listdir(self.carpeta_guardar_proyectos)
            if os.path.isdir(os.path.join(self.carpeta_guardar_proyectos, f))
        ]
        
        self.dlg.combo_created_projects.clear()
        self.dlg.combo_created_projects.addItems(project_names)

            
        if self.dlg.name_of_project.text() == "": #we put the last modified folder
            folders = [
                os.path.join(self.carpeta_guardar_proyectos, f)
                for f in os.listdir(self.carpeta_guardar_proyectos)
                if os.path.isdir(os.path.join(self.carpeta_guardar_proyectos, f))
            ]

            # Carpeta más recientemente modificada
            latest_folder = max(folders, key=os.path.getmtime)
            # Solo el nombre (sin ruta completa)
            latest_folder_name = os.path.basename(latest_folder)
            self.dlg.combo_created_projects.setCurrentIndex([x.lower() for x in project_names].index(latest_folder_name.lower()))
            
        else:
            #We put lower because the creatoin of folders is not case sensitive and the .index is case sensitive. 
            self.dlg.combo_created_projects.setCurrentIndex([x.lower() for x in project_names].index(self.dlg.name_of_project.text().lower()))
        
        #In sensitivity
        self.sensitivity_dialog.project_sensitivity.clear()
        self.sensitivity_dialog.project_sensitivity.addItems(project_names)
        if self.dlg.name_of_project.text() == "": #we put the last modified folder
            self.sensitivity_dialog.project_sensitivity.setCurrentIndex([x.lower() for x in project_names].index(latest_folder_name.lower()))
        else:
            #We put lower because the creatoin of folders is not case sensitive and the .index is case sensitive. 
            self.sensitivity_dialog.project_sensitivity.setCurrentIndex([x.lower() for x in project_names].index(self.dlg.name_of_project.text().lower()))
        
        #In calibration
        self.dlg_calibration.project_calibration.clear()
        self.dlg_calibration.project_calibration.addItems(project_names)
        if self.dlg.name_of_project.text() == "": #we put the last modified folder
            self.dlg_calibration.project_calibration.setCurrentIndex([x.lower() for x in project_names].index(latest_folder_name.lower()))
        else:
            #We put lower because the creatoin of folders is not case sensitive and the .index is case sensitive. 
            self.dlg_calibration.project_calibration.setCurrentIndex([x.lower() for x in project_names].index(self.dlg.name_of_project.text().lower()))
        
        
        #In scenario analysis
        if update_scenario:
            layout = self.dlg_scenario_analysis.frame.layout()
            
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.blockSignals(True)   #evita que emita señales
                        widget.deleteLater()
            
            self.update_available_projects_scenario()
        
            
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
        dic_search_check = {self.inputs.l_3:self.inputs.checkBox,self.inputs.l_5:self.inputs.checkBox_2,self.inputs.l_10:self.inputs.checkBox_3,self.inputs.l_41:self.inputs.checkBox_4,self.inputs.l_13:self.inputs.checkBox_5}
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
        self.ctopagnps.label_13.setToolTip(self.tr("This keyword allows the user to specify the format of the input DEM data. \n There are currently only two formats allowed. Optional; the default value of “0” will be assumed. \n0 = ASCII raster grid format (ASC input format) - (DEFAULT=0, if blank or keyword not used.) \n1 = one value per record in row-major order (original “DEDNM.INP” input format)"))
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
        self.ctopagnps.label_16.setToolTip(self.tr("This optional keyword allows the user to specify which modules are to be executed.\nOptions:\n“0” indicates that all modules are to be executed in sequence (DEDNM, RASPRO, RASFOR, AGFLOW, PEG,\nand AGBUF). This value supersedes all other options listed below.\n“1” indicates that only DEDNM is to be executed.\n“2” indicates that only DEDNM and RASPRO are to be executed.\n“3” indicates that only DEDNM, RASPRO, and RASFOR are to be executed.\n“4” indicates that only AGFLOW is to be executed.\n“5” indicates that only PEG is to be executed.\n“6” indicates that only AGBUF is to be executed.\n“7” indicates that only AGWET is to be executed.\n“8” indicates that only CONCEPTS is to be executed.\n“9” indicates that only POTHOLE is to be executed.\nMultiple options may be combined. For example:\n“56” (modules PEG and AGBUF will be executed.)\n“012” (all modules will be executed because “0” supersedes all other options.)"))
        self.ctopagnps.label_23.setToolTip(self.tr("This optional keyword allows the user to specify whether all output files produced will be in a single folder or\nin an internally defined folder structure. If “OUTPUT” is used with a value of “0”, or the value is left blank,\nthen the output files will be written to the following relative path:\nIf “OUTPUT” is used with a value of “1”, or the value is left blank, then all of the output files will be written to\nfolder from which TopAGNPS was invoked\nThe default value of “1” will be assumed."))
        self.ctopagnps.label_24.setToolTip(self.tr("This keyword allows the user to specify that the “intermediate” output files produced from a previous run will\nbe used as input rather than TopAGNPS having to regenerate them.\nOptional; the default value of “0” will be assumed.\n0 = do not use intermediate files - (DEFAULT=0, if blank or keyword not used.)\n1 = use intermediate output files from previous run as input"))
        self.ctopagnps.label_25.setToolTip(self.tr("This optional keyword allows the user to specify the location to the “intermediate” output files produced from a\nprevious run that will be used as input to TopAGNPS.\nThe default path will be the path associated with the “OUTPUT” keyword (see the “OUTPUT” keyword\ndescription above)."))
        
        
        #PEG
        self.cpeg.label.setToolTip(self.tr("csv-formatted input file containing PEG point locations to be read in and processed."))
        self.cpeg.label_2.setToolTip(self.tr("Threshold based on a CTI value"))
        self.cpeg.label_3.setToolTip(self.tr("Threshold based on a percent value"))
        self.cpeg.label_5.setToolTip(self.tr("This keyword allows the user to select how drainage area to the PEG points are displayed.\nThis keyword is optional. The acceptable values are '0' and '1'. A value of '0' indicates that the\n display of peg point drainage areas may overlap other peg points and their associated drainage\n areas. A value of '1' indicates that the display of peg point drainage areas may not overlap other\n peg points and their associated drainage areas.\nOptions: 0 or 1; DEFAULT = 0"))
        self.cpeg.label_6.setToolTip(self.tr("This keyword allows the user to select which PEG point drainage areas are to be displayed.\nThis keyword is optional. The acceptable values are '0', '1', or '2'. A value of '0' indicates that\n all valid peg point drainage areas will be displayed. A value of '1' indicates that only valid cell-\n located peg point drainage areas will be displayed. A value of '2' indicates that only valid reach-\n located peg point drainage areas will be displayed.\nOptions: 0, 1, or 2; DEFAULT = 0."))
        self.cpeg.label_7.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the spatial files created by\n DEDNM, RASPRO, RASFOR, and AgFlow are located. This path will also be used for spatial\n output files created by PEG."))
        self.cpeg.label_8.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the csv-formatted output files\ncreated by PEG will be written."))
        #AGBUF
        self.cagbuf.label.setToolTip(self.tr("Name and location of the spatial buffer layer that is to be used"))
        self.cagbuf.label_2.setToolTip(self.tr("Name and location of the spatial vegetation layer that is to be used"))
        self.cagbuf.label_3.setToolTip(self.tr("Value that was assigned as forest in the spatial vegetation layer"))
        self.cagbuf.label_4.setToolTip(self.tr("Value that was assigned as grass in the spatial vegetation layer"))
        self.cagbuf.label_5.setToolTip(self.tr("Threshold value for the cells in number of rasters"))
        self.cagbuf.label_6.setToolTip(self.tr("Threshold value for the reaches"))
        self.cagbuf.label_7.setToolTip(self.tr("Output units, SI or English, for the “AGBUF_AnnAGNPS.csv” file. \n A value of “1” indicates SI units and a value of “0” indicates English units"))
        self.cagbuf.label_9.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the spatial files created by\nDEDNM, RASPRO, RASFOR, and AgFlow are located. This path will also be used for spatial output\nfiles created by AGBUF."))
        self.cagbuf.label_10.setToolTip(self.tr("This optional keyword allows the user to specify the path to where any csv-formatted input files\nand the csv-formatted output files created by AGBUF will be written."))
        
        #AGFLOW
        self.agflow.label_4.setToolTip(self.tr("It's the code for which TopAGNPS output slope file is to be used for calculating each\nrasters LS-factor. A '1' will use the flow vector slope file (FVSLOP.ASC); a '2' will use the terrain slope file\n(TSLOPE.ASC); and a '3' will use the hydraulic slope file (HSLOPE.ASC). A 'blank' defaults to '1'"))
        self.agflow.label_5.setToolTip(self.tr("It's a real number for the maximum drainage area before concentrated flow begins\n(and accumulated sheet & rill erosion cease). A “blank” defaults to 0.99 ha"))
        self.agflow.label_6.setToolTip(self.tr("It's a real number for the maximum profile length before deposition begins and\nsheet & rill erosion along this particular profile path ceases. A “blank” defaults to 300 m."))
        self.agflow.label_7.setToolTip(self.tr("It's a real number for the maximum profile slope-angle which is meant to be used along with those structural conservation\npractices that actually decrease the slope-angle such as terraces. A “blank” defaults to “no limit” which should be\nused for most alternatives especially for natural conditions."))
        
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
        self.cconcepts.label_4.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the spatial files created by \nDEDNM, RASPRO, RASFOR, and AgFlow are located."))
        self.cconcepts.label_5.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the csv-formatted output files \ncreated by CONCEPTS will be written."))
        #POTHOLE
        self.cpothole.label.setToolTip(self.tr("This optional keyword allows the user to designate if potholes will be identified and processed. \n If this parameter is not present in the control file or if the value for this parameter is blank then the default \n value is 0 meaning that potholes will be identified."))
        self.cpothole.label_2.setToolTip(self.tr("This optional keyword allows the user to designate the minimum area in hectares that is required \n for a pothole to be considered valid and processed for reporting purposes; that is, \n the minimum surface area threshold has been met."))
        self.cpothole.label_4.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the spatial files created by\n DEDNM, RASPRO, RASFOR, and AgFlow are located. This path will also be used for spatial\noutput files created by POTHOLE"))
        self.cpothole.label_5.setToolTip(self.tr("This optional keyword allows the user to specify the path to where the csv-formatted output files\n created by POTHOLE will be written."))

        #Searcher of documents in AnnAGNPS inputs
        for i in self.dic_lines_search.values():
            i.setToolTip(self.tr("Search document"))
        #Create documents
        for i in self.dic_botones.keys():
            i.setToolTip(self.tr("Create CSV file"))
        #Modify annagnps inputs with table
        for i in self.table_buttons:
            i.setToolTip(self.tr("Modify input"))
        
    def annagnps_inputs(self,section):
        #Metod to add annangps inputs in the dialog depending on section selection
        
        #Delete all elements of vertical layout of scroll area
        while self.sensitivity_dialog.verticalLayout_2.count():
            child = self.sensitivity_dialog.verticalLayout_2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        #Add elements depending on selection
        #Import master file to check if the files exist
        try:
            master_file = self.carpeta_guardar_proyectos+f"\\{self.sensitivity_dialog.project_sensitivity.currentText()}\\Processing_inputs\\annagnps_master.csv"
            project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")
        except:
            project_df = "nan"
        
        #Add buttons
        if section == "Spatial":
            inputs_spatial = ["TopAgnps","Ephemeral Gully","Riparian Buffers","Hydraulics and hydrology \nfor cells and reaches","Wetland","Pothole"]
            dic = {"TopAgnps":["Pixel Size","Critical Source Area","Minimum Source Channel \nLength"],"Ephemeral Gully":["Absolute CTI","Relative CTI"],"Riparian Buffers":["Cell Threshold","Reach Threshold"],"Hydraulics and hydrology \nfor cells and reaches":["Drainage area \nto concentrated flow","Maximum profile length \nuntil deposition","Maximum Profile Slope"],"Wetland":["Wetness Index Threshold","Erosion Index Threshold","Drainage Area Threshold","Maximum Wetland Ratio","Minimum Wetland Ratio","Barrier Height","Barrier Height Increment","Barrier Height Maximum","Buffer width"],"Pothole":["Pothole Surface Area"]}
            for nombre in inputs_spatial:
                boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents)
                boton.setObjectName(nombre)
                self.sensitivity_dialog.verticalLayout_2.addWidget(boton)
                política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(política_tamaño)
                boton.clicked.connect(lambda _, b = dic[nombre]: self.annagnps_parameters(b))
        if section == "Watershed":
            inputs_watershed = ["Aquaculture pond","Cell","Classic Gully","Ephemeral Gully","Feedlot","Field Pond", "Impoundment", "Point Source", "Reach", "Watershed", "Wetland"]
            dic = {"Aquaculture pond":["Pond area","Pond Depth", "Seepage Rate", "Sediment Delivery Ratio Pond", "Organic Carbon \nCalibration Factor Pond", "Nitrogen Calibration Factor Pond", "Phosphorus Calibration Factor Pond", "Erosion Calibration Factor Pond"],"Cell":["Sheet flow Manning’s n","Concentrated flow \nhydraulic depth","Concentrated flow Manning’s n","Delivery Ratio Pond","Constant USLE C factor","Constant USLE P factor","All Organic Carbon \nCalibration Factor","All Nitrogen Calibration Factor","All Phosphorus Calibration Factor","Sheet and Rill Erosion \nCalibration Factor","Gullies Erosion Calibration Factor"],"Classic Gully":["Head Cut Depth","Erosion Coefficient","Erosion Exponent","Delivery Ratio Gully","Organic Carbon \nCalibration Factor Gully","Nitrogen Calibration Factor Gully","Phosphorus Calibration Factor Gully","Erosion Calibration Factor Gully"],"Ephemeral Gully":["Critical Shear Stress \nEphemeral Gully","Erosion Depth","Delivery Ratio Ephemeral Gully","Manning’s n Ephemeral Gully","Re Plant Period","Organic Carbon","Nitrogen","Phosphorus","Erosion","Headcut detachment leading \ncoefficient a","Headcut erodibility \nleading coefficient a","Headcut detachment exponent \ncoefficient b","Headcut erodibility exponent \ncoefficient b","Maximum Buffer Trapping \nEfficiency TE m"],"Feedlot":["Open Area","Paved Ratio","Roof Area","Upslope Area","Feedlot Initial N","Feedlot Initial P","Feedlot Initial OrgC","Delta N","Delta P","Delta OrgC","Feedlot Max N","Feedlot Max P","Feedlot Max OrgC","Feedlot Pack N","Feedlot Pack P","Feedlot Pack OrgC","Organic Carbon Calibration \nFactor Feedlot","Nitrogen Calibration \nFactor Feedlot","Phosphorus Calibration \nFactor Feedlot","Erosion Calibration \nFactor Feedlot","Cell Buffer Length"],"Field Pond":["Field Pond area","Number of rotation years","Number gate operations","Delivery Ratio Field Pond","Volume of release water","Drain Time","Release rate","Sediment Concentration","Clay content Field Pond","Silt content Field Pond","Organic Carbon Calibration Factor Field Pond","Nitrogen Calibration Factor Field Pond","Phosphorus Calibration Factor Field Pond","Erosion Calibration Factor Field Pond"], "Impoundment":["Impoundment Infiltration","Impoundment Seepage","Permanent Pool Depth","Impound Volume Coefficient","Impound Volume Exponent","Impound Discharge Coefficient","Impound Discharge Exponent","Sediment Clean Out Depth","Sediment Clean Out Year"], "Point Source":["Point Flow","Point Nitrogen","Point Phosphorus","Point Organic Carbon","Organic Carbon Calibration Factor","Nitrogen Calibration Factor","Phosphorus Calibration Factor","Erosion Calibration Factor"], "Reach":["Reach Manning’s n","Reach Flow Depth","Valley Width","Valley n","Delivery Ratio Reach"], "Watershed":["Latitude","Longitude"], "Wetland":["Wetland Area","Initial Water Depth","Minimum Water Depth","Maximum Water Depth","Water Temperature","Potential Daily Infiltration","Weir Coefficient","Weir Width","Weir Height","Soluble N Concentration","Nitrate Loss Rate","Nitrate Loss Rate Coefficient","Temperature Coefficient","Weir Exponent"]}
            for nombre in inputs_watershed:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.sensitivity_dialog.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.annagnps_parameters(b))
        if section == "General":
            inputs_general = ["Management Aquaculture \n Pond Schedule", "Contour", "Crop", "Crop Growth", "Feedlot Management","Fertilizer application", "Fertilizer reference", "Geology", "Hydraulic Geometry", "Irrigation Application", "Management Field", "Management Operation", "Management Schedule", "Non-crop","Pesticide Application", "Pesticide Reference","Reach Nutrient Half-life", "Riparian Buffer", "Runoff Curve", "Soil", "Soil Layers", "Strip Crop", "Tile Drain"]
            dic = {"Management Aquaculture \n Pond Schedule":["Maximum Pool Depth","Minimum Pool Depth","Fill/Release Volume","Fill/Drain Time","Fill/Release Rate","Fill/Drain All","Total Sediment Concentration","Clay Content Pond Schedule","Silt Content Pond Schedule","Total Nitrogen","Dissolved Nitrogen","Total Phosphorus","Dissolved Phosphorus","Sediment Concentration—Winter","Total Nitrogen—Winter","Dissolved Nitrogen—Winter","Total Phosphorus—Winter","Dissolved Phosphorus—Winter","Sediment Concentration—Spring","Total Nitrogen—Spring","Dissolved Nitrogen—Spring","Total Phosphorus—Spring","Dissolved Phosphorus—Spring","Sediment Concentration—Summer","Total Nitrogen—Summer","Dissolved Nitrogen—Summer","Total Phosphorus—Summer","Dissolved Phosphorus—Summer","Sediment Concentration—Autumn","Total Nitrogen—Autumn","Dissolved Nitrogen—Autumn","Total Phosphorus—Autumn","Dissolved Phosphorus—Autumn"], "Contour":["Furrow Slope"], "Crop":["Yield Units Harvested per Area","Residue Mass Ratio","Surface decomposition Crop","Sub-surface decomposition Crop","USLE C-Factor Crop","Moisture Depletion","Crop Residue_30%","Crop Residue_60%","Crop Residue_90%","Yield Unit Mass","Harvest C-N Ratio","N Uptake","P Uptake","Harvest C-P Ratio","Growth Time Ini","Growth Time Dev","Growth Time Mat","Basal Crop Coefficient (“Kcb-ini”) crop","Basal Crop Coefficient (“Kcb-mid”) crop","Basal Crop Coefficient (“Kcb-end”) crop"], "Crop Growth":["Root Mass","Canopy Cover","Rain Fall Height"], "Feedlot Management":["Pack Remove Ratio","Pack Start N","Pack Start P","Pack Start OrgC","Pack Change N","Pack Change P","Pack Change OrgC"],"Fertilizer application":["Fertilizer Rate"], "Fertilizer reference":["Fertilizer Inorganic N","Fertilizer Organic N","Fertilizer Inorganic P","Fertilizer Organic P","Fertilizer Organic Matter"], "Geology":["Delay Time","Water Table","Aquifer Saturated \nHydraulic Conductivity","K-vadose Saturated \nHydraulic Conductivity","Aquifer Porosity","Aquifer Field Capacity","Aquifer Specific Yield","Aquifer Thickness","Aquifer Soluble Nitrogen","Aquifer Soluble Phosphorus"], "Hydraulic Geometry":["Channel Length Coefficient","Channel Length Exponent","Channel Width Coefficient","Channel Width Exponent","Channel Depth Coefficient","Channel Depth Exponent","Valley Width Coefficient","Valley Width Exponent"], "Irrigation Application":["Cycle Duration","Amount Lost","Application Rate","Tailwater Recovery","Depletion Lower Limit","Application Amount","Area Fraction","Interval Number","Interval Days","Chemical Multiple","Sediment Rate","Depletion Upper Limit"], "Management Field":["Percent Rock Cover","Random Roughness","Terrace Horizontal Distance","Terrace grade"], "Management Operation":["Residue Cover Remaining","Residue Weight Remaining","Area Disturbed","Initial Random Roughness","Final Random Roughness","Operation Tillage Depth","Added Surface Residue","Surface Decomposition \nmanagement","Sub-surface Decomposition \nmanagement","Surface Residue_30%","Surface Residue_60%","Surface Residue_90%"], "Management Schedule":["Post Event Manning’s n","Post Event Surface Constant","Operation Residue Change","Tile Drain Controlled Depth"], "Non-crop":["Annual Root Mass","Annual Cover Ratio","Annual Rain Fall Height","Surface Residue Cover","USLE C-Factor Non Crop","Basal Crop Coefficient (“Kcb-mid”) Non Crop"],"Pesticide Application":["Pesticide Rate","Pesticide Depth","Pesticide Foliage Fraction","Pesticide Soil Fraction"], "Pesticide Reference":["Pesticide Solubility","Pesticide Partition","Pesticide Soil Half-life","Pesticide Foliage Half-life","Pesticide Washoff","Metabolite Transformation","Pesticide Reach Half-life"],"Reach Nutrient Half-life":["Reach Nitrogen Half-life","Reach Phosphorus Half-life","Reach Organic Carbon Half-life"], "Riparian Buffer":["Slope","Maximum Trapping \nEfficiency “TE-m”","Effective Buffer Width","Effective Concentrated \nFlow Width","Drainage Area to Upstream \nPortion of Buffer","Actual Trapping Efficiency \n“TE-a” Clay","Actual Trapping Efficiency \n“TE-a” Silt","Actual Trapping Efficiency \n“TE-a” Sand","Actual Trapping Efficiency \n“TE-a” Sm Agg","Actual Trapping Efficiency \n“TE-a” Lg Agg","Fraction Trapped “TE-ps” Clay","Fraction Trapped “TE-ps” Silt","Fraction Trapped “TE-ps” Sand","Fraction Trapped “TE-ps” Sm Agg","Fraction Trapped “TE-ps” Lg Agg"], "Runoff Curve":["Curve Number “A”","Curve Number “B”","Curve Number “C”","Curve Number “D”"], "Soil":["K-factor","Albedo","Time to consolidation","Impervious Depth","Specific Gravity"], "Soil Layers":["Layer Depth","Bulk Density","Clay Ratio","Silt Ratio","Sand Ratio","Rock Ratio","Very Fine Sand Ratio","CaCO3","Saturated Conductivity","Field Capacity","Wilting Point","Base Saturation","Unstable Aggregate Ratio","pH","Organic Matter Ratio","Organic N Ratio","Inorganic N Ratio","Organic P Ratio","Inorganic P Ratio"], "Strip Crop":["P Factor","Sediment Delivery Ratio Strip Crop"], "Tile Drain":["Drain Rate","Invert Depth"]}
            for nombre in inputs_general:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.sensitivity_dialog.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.annagnps_parameters(b))
        if section == "Climate":
            inputs_climate = ["Climate Station", "EI Percentage"]
            dic = {"Climate Station":["Station Latitude","Station Longitude","Station Elevation","Adiabatic Air Temperature \nLapse Rate","Precipitation Nitrogen","Elevation Difference (1)","Elevation Rain Factor (1)","Elevation Difference (2)","Elevation Rain Factor (2)","2 Yr 24 Hr Precipitation","Rainfall Calibration or Areal \nCorrection Coefficient","Areal Rainfall \nCorrection Exponent","Minimum interception \nevaporation station","Maximum interception \nevaporation station"], "EI Percentage":["EI_Pct_01","EI_Pct_02","EI_Pct_03","EI_Pct_04","EI_Pct_05","EI_Pct_06","EI_Pct_07","EI_Pct_08","EI_Pct_09","EI_Pct_10","EI_Pct_11","EI_Pct_12","EI_Pct_13","EI_Pct_14","EI_Pct_15","EI_Pct_16","EI_Pct_17","EI_Pct_18","EI_Pct_19","EI_Pct_20","EI_Pct_21","EI_Pct_22","EI_Pct_23","EI_Pct_24"]}
            for nombre in inputs_climate:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.sensitivity_dialog.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.annagnps_parameters(b))
        if section == "Simulation":
            inputs_simulation = ["Global IDs Factors \n and Flags","Pesticide Initial Conditions","PL Calibration","RCN Calibration","Simulation Period","Soil Initial Conditions"]
            dic = {"Global IDs Factors \n and Flags":["Headcut detachment leading coefficient (a)","Headcut detachment exponent coefficient (b)","Headcut erodibility leading coefficient (a)","Headcut erodibility exponent coefficient (b)","Minimum Interception Evaporation Global","Maximum Interception Evaporation Global","Detention Coefficient “a”","Detention Coefficient “b”","RCN Convergence Tolerance","RCN Maximum Number of Iterations","Available Soil Moisture Ratio for AMC II","Maximum Available Sediment Concentration for Sheet Flow","Maximum Available Sediment Concentration for Concentrated Flow","Critical Shear Stress"],"Pesticide Initial Conditions":["Crop Initial Pesticide Amount 1","Crop Initial Pesticide Amount 2","Non-crop Initial Pesticide Amount 1","Non-crop Initial Pesticide Amount 2"],"PL Calibration":["Organic carbon from all sources","Organic carbon from sheet & rill","Organic carbon from feedlot","Organic carbon from point source","Organic carbon from gully","Organic carbon from pond","Organic carbon from irrigation","Nitrogen from all sources","Nitrogen from sheet & rill","Nitrogen from feedlot","Nitrogen from point source","Nitrogen from gully","Nitrogen from pond","Nitrogen from irrigation","Phosphorus from all sources","Phosphorus from sheet & rill","Phosphorus from feedlot","Phosphorus from point source","Phosphorus from gully","Phosphorus from pond","Phosphorus from irrigation","Sediment from all sources","Sediment from sheet & rill","Sediment from feedlot","Sediment from point source","Sediment from gully","Sediment from pond","Sediment from irrigation"],"RCN Calibration":["Target Average Annual Direct Runoff Load","RCN Retention factor","Reach Ratio","Available Soil Moisture, AMC-II"],"Simulation Period":["Rainfall factor","10-yr EI","EI Number","Initialization Method Code"],"Soil Initial Conditions":["Inorganic_N_1" ,"Inorganic_N_2", "Inorganic_P_1","Inorganic_P_2", "Soil_Moisture_1","Soil_Moisture_2", "Organic_Matter_1","Organic_Matter_2","Organic_N_1","Organic_N_2", "Organic_P_1","Organic_P_2","Surface Residue","Manning’s n","Snow Depth","Snow Density","Surface Constant"]}
            for nombre in inputs_simulation:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.sensitivity_dialog.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.annagnps_parameters(b))
    
    def check_if_input_present_in_master(self,fichero,project_df):
        """Method to check if a file is present in a master file for the inputs of sensitivity and calibration"""
        dictionary_master_file = {"Aquaculture pond":"Aquaculture Pond Data",
                               "Management Aquaculture \n Pond Schedule":"Aquaculture Schedule Data","Cell":"Cell Data","Classic Gully":"Classic Gully Data",
                               "Contour":"Contour Data","Crop":"Crop Data","Crop Growth":"Crop Growth Data",
                               "Ephemeral Gully":"Ephemeral Gully Data","Feedlot":"Feedlot Data","Feedlot Management":"Feedlot Management Data",
                               "Fertilizer application":"Fertilizer Application Data","Fertilizer reference":"Fertilizer Reference Data",
                               "Field Pond":"Field Pond Data","Geology":"Geology Data",
                               "Global IDs Factors \n and Flags":"Global IDs Factors and Flags Data",
                               "Hydraulic Geometry":"Hydraulic Geometry Data","Impoundment":"Impoundment Data",
                               "Irrigation Application":"Irrigation Application Data","Management Field":"Management Field Data",
                               "Management Operation":"Management Operation Data","Management Schedule":"Management Schedule Data",
                               "Non-crop":"Non-Crop Data",
                               "Pesticide Application":"Pesticide Application Data","Pesticide Initial Conditions":"Pesticide Initial Conditions Data",
                               "Pesticide Reference":"Pesticide Reference Data","PL Calibration":"PL Calibration Data",
                               "Point Source":"Point Source Data","RCN Calibration":"RCN Calibration Data","Reach":"Reach Data",
                               "Reach Nutrient Half-life":"Reach Nutrient Half-life Data","Runoff Curve":"Runoff Curve Number Data",
                               "Simulation Period":"Simulation Period Data","Soil":"Soil Data","Soil Layers":"Soil Layer Data",
                               "Soil Initial Conditions":"Soil Initial Conditions Data","Strip Crop":"Strip Crop Data",
                               "Tile Drain":"Tile Drain Data","Watershed":"Watershed Data","EI Percentage":"EI Pct Data",
                               "Climate Station":"CLIMATE DATA - STATION",
                               "Wetland":"Wetland Data","Riparian Buffer":"Riparian Buffer Data"}
        
        
        if type(project_df) == str:
            return True
        
        if dictionary_master_file[fichero] in project_df.iloc[:, 0].values:
            return True
        else:
            return False
        
        
        
        def modify_input(proyecto,name_master,column,new_columns,name_new_file):
            master_file = self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs\\annagnps_master.csv"
            project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")

            if name_master in project_df.iloc[:,0].values:
                file = Path(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]==name_master].iloc[0,1])
                data = pd.read_csv(file,encoding = "ISO-8859-1",delimiter=",")
                # Eliminar espacios al inicio y final de los nombres de columnas
                data.columns = data.columns.str.strip()
                data[column].iloc[0] = "T"
                data.to_csv(file, index=False, float_format='%.5f')
                
            else:
                columns = new_columns
                data = pd.DataFrame(columns=columns, data=[[""] * len(columns)])
                data[column].iloc[0] = "T"
                nombre = name_new_file
                file = Path(self.carpeta_guardar_proyectos+f"\\{proyecto}\\Processing_inputs"+"\\simulation\\"+f"{nombre}.csv")
                data.to_csv(file, index=False, float_format='%.5f')
                project_df.loc[len(project_df)] = [name_master, f".\simulation\{nombre}.csv"]
                project_df.to_csv(master_file, index=False, float_format='%.5f')
                
                
                
    
    
    def calibration_inputs(self,section):
        #Metod to add calibration inputs in the dialog depending on section selection
        
        #Delete all elements of vertical layout of scroll area
        while self.dlg_calibration.verticalLayout_2.count():
            child = self.dlg_calibration.verticalLayout_2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        #Add elements depending on selection
        
        #Import master file to check if the files exist
        try:
            master_file = self.carpeta_guardar_proyectos+f"\\{self.sensitivity_dialog.project_sensitivity.currentText()}\\Processing_inputs\\annagnps_master.csv"
            project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")
        except:
            project_df = "nan"
            
        #Add buttons
        if section == "Spatial":
            inputs_spatial = ["TopAgnps","Ephemeral Gully","Riparian Buffers","Hydraulics and hydrology \nfor cells and reaches","Wetland","Pothole"]
            dic = {"TopAgnps":["Pixel Size","Critical Source Area","Minimum Source Channel \nLength"],"Ephemeral Gully":["Absolute CTI","Relative CTI"],"Riparian Buffers":["Cell Threshold","Reach Threshold"],"Hydraulics and hydrology \nfor cells and reaches":["Drainage area \nto concentrated flow","Maximum profile length \nuntil deposition","Maximum Profile Slope"],"Wetland":["Wetness Index Threshold","Erosion Index Threshold","Drainage Area Threshold","Maximum Wetland Ratio","Minimum Wetland Ratio","Barrier Height","Barrier Height Increment","Barrier Height Maximum","Buffer width"],"Pothole":["Pothole Surface Area"]}
            for nombre in inputs_spatial:
                boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents)
                boton.setObjectName(nombre)
                self.dlg_calibration.verticalLayout_2.addWidget(boton)
                política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                boton.setSizePolicy(política_tamaño)
                boton.clicked.connect(lambda _, b = dic[nombre]: self.calibration_parameters(b))
        if section == "Watershed":
            inputs_watershed = ["Aquaculture pond","Cell","Classic Gully","Ephemeral Gully","Feedlot","Field Pond", "Impoundment", "Point Source", "Reach", "Watershed", "Wetland"]
            dic = {"Aquaculture pond":["Pond area","Pond Depth", "Seepage Rate", "Sediment Delivery Ratio Pond", "Organic Carbon \nCalibration Factor Pond", "Nitrogen Calibration Factor Pond", "Phosphorus Calibration Factor Pond", "Erosion Calibration Factor Pond"],"Cell":["Sheet flow Manning’s n","Concentrated flow \nhydraulic depth","Concentrated flow Manning’s n","Delivery Ratio Pond","Constant USLE C factor","Constant USLE P factor","All Organic Carbon \nCalibration Factor","All Nitrogen Calibration Factor","All Phosphorus Calibration Factor","Sheet and Rill Erosion \nCalibration Factor","Gullies Erosion Calibration Factor"],"Classic Gully":["Head Cut Depth","Erosion Coefficient","Erosion Exponent","Delivery Ratio Gully","Organic Carbon \nCalibration Factor Gully","Nitrogen Calibration Factor Gully","Phosphorus Calibration Factor Gully","Erosion Calibration Factor Gully"],"Ephemeral Gully":["Critical Shear Stress \nEphemeral Gully","Erosion Depth","Delivery Ratio Ephemeral Gully","Manning’s n Ephemeral Gully","Re Plant Period","Organic Carbon","Nitrogen","Phosphorus","Erosion","Headcut detachment leading \ncoefficient a","Headcut erodibility \nleading coefficient a","Headcut detachment exponent \ncoefficient b","Headcut erodibility exponent \ncoefficient b","Maximum Buffer Trapping \nEfficiency TE m"],"Feedlot":["Open Area","Paved Ratio","Roof Area","Upslope Area","Feedlot Initial N","Feedlot Initial P","Feedlot Initial OrgC","Delta N","Delta P","Delta OrgC","Feedlot Max N","Feedlot Max P","Feedlot Max OrgC","Feedlot Pack N","Feedlot Pack P","Feedlot Pack OrgC","Organic Carbon Calibration \nFactor Feedlot","Nitrogen Calibration \nFactor Feedlot","Phosphorus Calibration \nFactor Feedlot","Erosion Calibration \nFactor Feedlot","Cell Buffer Length"],"Field Pond":["Field Pond area","Number of rotation years","Number gate operations","Delivery Ratio Field Pond","Volume of release water","Drain Time","Release rate","Sediment Concentration","Clay content Field Pond","Silt content Field Pond","Organic Carbon Calibration Factor Field Pond","Nitrogen Calibration Factor Field Pond","Phosphorus Calibration Factor Field Pond","Erosion Calibration Factor Field Pond"], "Impoundment":["Impoundment Infiltration","Impoundment Seepage","Permanent Pool Depth","Impound Volume Coefficient","Impound Volume Exponent","Impound Discharge Coefficient","Impound Discharge Exponent","Sediment Clean Out Depth","Sediment Clean Out Year"], "Point Source":["Point Flow","Point Nitrogen","Point Phosphorus","Point Organic Carbon","Organic Carbon Calibration Factor","Nitrogen Calibration Factor","Phosphorus Calibration Factor","Erosion Calibration Factor"], "Reach":["Reach Manning’s n","Reach Flow Depth","Valley Width","Valley n","Delivery Ratio Reach"], "Watershed":["Latitude","Longitude"], "Wetland":["Wetland Area","Initial Water Depth","Minimum Water Depth","Maximum Water Depth","Water Temperature","Potential Daily Infiltration","Weir Coefficient","Weir Width","Weir Height","Soluble N Concentration","Nitrate Loss Rate","Nitrate Loss Rate Coefficient","Temperature Coefficient","Weir Exponent"]}
            for nombre in inputs_watershed:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.dlg_calibration.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.calibration_parameters(b))
        if section == "General":
            inputs_general = ["Management Aquaculture \n Pond Schedule", "Contour", "Crop", "Crop Growth", "Feedlot Management","Fertilizer application", "Fertilizer reference", "Geology", "Hydraulic Geometry", "Irrigation Application", "Management Field", "Management Operation", "Management Schedule", "Non-crop","Pesticide Application", "Pesticide Reference","Reach Nutrient Half-life", "Riparian Buffer", "Runoff Curve", "Soil", "Soil Layers", "Strip Crop", "Tile Drain"]
            dic = {"Management Aquaculture \n Pond Schedule":["Maximum Pool Depth","Minimum Pool Depth","Fill/Release Volume","Fill/Drain Time","Fill/Release Rate","Fill/Drain All","Total Sediment Concentration","Clay Content Pond Schedule","Silt Content Pond Schedule","Total Nitrogen","Dissolved Nitrogen","Total Phosphorus","Dissolved Phosphorus","Sediment Concentration—Winter","Total Nitrogen—Winter","Dissolved Nitrogen—Winter","Total Phosphorus—Winter","Dissolved Phosphorus—Winter","Sediment Concentration—Spring","Total Nitrogen—Spring","Dissolved Nitrogen—Spring","Total Phosphorus—Spring","Dissolved Phosphorus—Spring","Sediment Concentration—Summer","Total Nitrogen—Summer","Dissolved Nitrogen—Summer","Total Phosphorus—Summer","Dissolved Phosphorus—Summer","Sediment Concentration—Autumn","Total Nitrogen—Autumn","Dissolved Nitrogen—Autumn","Total Phosphorus—Autumn","Dissolved Phosphorus—Autumn"], "Contour":["Furrow Slope"], "Crop":["Yield Units Harvested per Area","Residue Mass Ratio","Surface decomposition Crop","Sub-surface decomposition Crop","USLE C-Factor Crop","Moisture Depletion","Crop Residue_30%","Crop Residue_60%","Crop Residue_90%","Yield Unit Mass","Harvest C-N Ratio","N Uptake","P Uptake","Harvest C-P Ratio","Growth Time Ini","Growth Time Dev","Growth Time Mat","Basal Crop Coefficient (“Kcb-ini”) crop","Basal Crop Coefficient (“Kcb-mid”) crop","Basal Crop Coefficient (“Kcb-end”) crop"], "Crop Growth":["Root Mass","Canopy Cover","Rain Fall Height"], "Feedlot Management":["Pack Remove Ratio","Pack Start N","Pack Start P","Pack Start OrgC","Pack Change N","Pack Change P","Pack Change OrgC"],"Fertilizer application":["Fertilizer Rate"], "Fertilizer reference":["Fertilizer Inorganic N","Fertilizer Organic N","Fertilizer Inorganic P","Fertilizer Organic P","Fertilizer Organic Matter"], "Geology":["Delay Time","Water Table","Aquifer Saturated \nHydraulic Conductivity","K-vadose Saturated \nHydraulic Conductivity","Aquifer Porosity","Aquifer Field Capacity","Aquifer Specific Yield","Aquifer Thickness","Aquifer Soluble Nitrogen","Aquifer Soluble Phosphorus"], "Hydraulic Geometry":["Channel Length Coefficient","Channel Length Exponent","Channel Width Coefficient","Channel Width Exponent","Channel Depth Coefficient","Channel Depth Exponent","Valley Width Coefficient","Valley Width Exponent"], "Irrigation Application":["Cycle Duration","Amount Lost","Application Rate","Tailwater Recovery","Depletion Lower Limit","Application Amount","Area Fraction","Interval Number","Interval Days","Chemical Multiple","Sediment Rate","Depletion Upper Limit"], "Management Field":["Percent Rock Cover","Random Roughness","Terrace Horizontal Distance","Terrace grade"], "Management Operation":["Residue Cover Remaining","Residue Weight Remaining","Area Disturbed","Initial Random Roughness","Final Random Roughness","Operation Tillage Depth","Added Surface Residue","Surface Decomposition \nmanagement","Sub-surface Decomposition \nmanagement","Surface Residue_30%","Surface Residue_60%","Surface Residue_90%"], "Management Schedule":["Post Event Manning’s n","Post Event Surface Constant","Operation Residue Change","Tile Drain Controlled Depth"], "Non-crop":["Annual Root Mass","Annual Cover Ratio","Annual Rain Fall Height","Surface Residue Cover","USLE C-Factor Non Crop","Basal Crop Coefficient (“Kcb-mid”) Non Crop"],"Pesticide Application":["Pesticide Rate","Pesticide Depth","Pesticide Foliage Fraction","Pesticide Soil Fraction"], "Pesticide Reference":["Pesticide Solubility","Pesticide Partition","Pesticide Soil Half-life","Pesticide Foliage Half-life","Pesticide Washoff","Metabolite Transformation","Pesticide Reach Half-life"],"Reach Nutrient Half-life":["Reach Nitrogen Half-life","Reach Phosphorus Half-life","Reach Organic Carbon Half-life"], "Riparian Buffer":["Slope","Maximum Trapping \nEfficiency “TE-m”","Effective Buffer Width","Effective Concentrated \nFlow Width","Drainage Area to Upstream \nPortion of Buffer","Actual Trapping Efficiency \n“TE-a” Clay","Actual Trapping Efficiency \n“TE-a” Silt","Actual Trapping Efficiency \n“TE-a” Sand","Actual Trapping Efficiency \n“TE-a” Sm Agg","Actual Trapping Efficiency \n“TE-a” Lg Agg","Fraction Trapped “TE-ps” Clay","Fraction Trapped “TE-ps” Silt","Fraction Trapped “TE-ps” Sand","Fraction Trapped “TE-ps” Sm Agg","Fraction Trapped “TE-ps” Lg Agg"], "Runoff Curve":["Curve Number “A”","Curve Number “B”","Curve Number “C”","Curve Number “D”"], "Soil":["K-factor","Albedo","Time to consolidation","Impervious Depth","Specific Gravity"], "Soil Layers":["Layer Depth","Bulk Density","Clay Ratio","Silt Ratio","Sand Ratio","Rock Ratio","Very Fine Sand Ratio","CaCO3","Saturated Conductivity","Field Capacity","Wilting Point","Base Saturation","Unstable Aggregate Ratio","pH","Organic Matter Ratio","Organic N Ratio","Inorganic N Ratio","Organic P Ratio","Inorganic P Ratio"], "Strip Crop":["P Factor","Sediment Delivery Ratio Strip Crop"], "Tile Drain":["Drain Rate","Invert Depth"]}
            for nombre in inputs_general:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.dlg_calibration.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.calibration_parameters(b))
        if section == "Climate":
            inputs_climate = ["Climate Station", "EI Percentage"]
            dic = {"Climate Station":["Station Latitude","Station Longitude","Station Elevation","Adiabatic Air Temperature \nLapse Rate","Precipitation Nitrogen","Elevation Difference (1)","Elevation Rain Factor (1)","Elevation Difference (2)","Elevation Rain Factor (2)","2 Yr 24 Hr Precipitation","Rainfall Calibration or Areal \nCorrection Coefficient","Areal Rainfall \nCorrection Exponent","Minimum interception \nevaporation station","Maximum interception \nevaporation station"], "EI Percentage":["EI_Pct_01","EI_Pct_02","EI_Pct_03","EI_Pct_04","EI_Pct_05","EI_Pct_06","EI_Pct_07","EI_Pct_08","EI_Pct_09","EI_Pct_10","EI_Pct_11","EI_Pct_12","EI_Pct_13","EI_Pct_14","EI_Pct_15","EI_Pct_16","EI_Pct_17","EI_Pct_18","EI_Pct_19","EI_Pct_20","EI_Pct_21","EI_Pct_22","EI_Pct_23","EI_Pct_24"]}
            for nombre in inputs_climate:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.dlg_calibration.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.calibration_parameters(b))
        if section == "Simulation":
            inputs_simulation = ["Global IDs Factors \n and Flags","Pesticide Initial Conditions","PL Calibration","RCN Calibration","Simulation Period","Soil Initial Conditions"]
            dic = {"Global IDs Factors \n and Flags":["Headcut detachment leading coefficient (a)","Headcut detachment exponent coefficient (b)","Headcut erodibility leading coefficient (a)","Headcut erodibility exponent coefficient (b)","Minimum Interception Evaporation Global","Maximum Interception Evaporation Global","Detention Coefficient “a”","Detention Coefficient “b”","RCN Convergence Tolerance","RCN Maximum Number of Iterations","Available Soil Moisture Ratio for AMC II","Maximum Available Sediment Concentration for Sheet Flow","Maximum Available Sediment Concentration for Concentrated Flow","Critical Shear Stress"],"Pesticide Initial Conditions":["Crop Initial Pesticide Amount 1","Crop Initial Pesticide Amount 2","Non-crop Initial Pesticide Amount 1","Non-crop Initial Pesticide Amount 2"],"PL Calibration":["Organic carbon from all sources","Organic carbon from sheet & rill","Organic carbon from feedlot","Organic carbon from point source","Organic carbon from gully","Organic carbon from pond","Organic carbon from irrigation","Nitrogen from all sources","Nitrogen from sheet & rill","Nitrogen from feedlot","Nitrogen from point source","Nitrogen from gully","Nitrogen from pond","Nitrogen from irrigation","Phosphorus from all sources","Phosphorus from sheet & rill","Phosphorus from feedlot","Phosphorus from point source","Phosphorus from gully","Phosphorus from pond","Phosphorus from irrigation","Sediment from all sources","Sediment from sheet & rill","Sediment from feedlot","Sediment from point source","Sediment from gully","Sediment from pond","Sediment from irrigation"],"RCN Calibration":["Target Average Annual Direct Runoff Load","RCN Retention factor","Reach Ratio","Available Soil Moisture, AMC-II"],"Simulation Period":["Rainfall factor","10-yr EI","EI Number","Initialization Method Code"],"Soil Initial Conditions":["Inorganic_N_1" ,"Inorganic_N_2", "Inorganic_P_1","Inorganic_P_2", "Soil_Moisture_1","Soil_Moisture_2", "Organic_Matter_1","Organic_Matter_2","Organic_N_1","Organic_N_2", "Organic_P_1","Organic_P_2","Surface Residue","Manning’s n","Snow Depth","Snow Density","Surface Constant"]}
            for nombre in inputs_simulation:
                if self.check_if_input_present_in_master(nombre,project_df):
                    boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents)
                    boton.setObjectName(nombre)
                    self.dlg_calibration.verticalLayout_2.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = dic[nombre]: self.calibration_parameters(b))
    
    def annagnps_parameters(self, parameters):
        #Metod to add parameters in the dialog depending on input selection
        #Delete all elements of vertical layout of scroll area
        while self.sensitivity_dialog.verticalLayout_3.count():
            child = self.sensitivity_dialog.verticalLayout_3.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        #Add elements
        for nombre in parameters:
            boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents_3)
            boton.setObjectName(nombre)
            self.sensitivity_dialog.verticalLayout_3.addWidget(boton)
            política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            boton.setSizePolicy(política_tamaño)
            boton.clicked.connect(lambda _, b = nombre: self.add_parameter_label(b))
    
    
    def calibration_parameters(self, parameters):
        #Metod to add parameters in the dialog depending on input selection
        #Delete all elements of vertical layout of scroll area
        while self.dlg_calibration.verticalLayout_3.count():
            child = self.dlg_calibration.verticalLayout_3.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        #Add elements
        for nombre in parameters:
            boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents_3)
            boton.setObjectName(nombre)
            self.dlg_calibration.verticalLayout_3.addWidget(boton)
            política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            boton.setSizePolicy(política_tamaño)
            boton.clicked.connect(lambda _, b = nombre: self.add_parameter_label_calibration(b))
    
    def add_sensitivity_table(self):
        #Metod to add sensitivity analysis parameters to table
        if self.sensitivity_dialog.table.columnCount() == 0:
            #Añadir columnas
            nombres_columnas = ["Parameter","Distribution","Distribution parameters","Row"]
            self.sensitivity_dialog.table.setColumnCount(len(nombres_columnas))
            self.sensitivity_dialog.table.setHorizontalHeaderLabels(nombres_columnas)
            #Cambiar el ancho de las columnas
            self.sensitivity_dialog.table.setColumnWidth(nombres_columnas.index("Parameter"), 180)
            self.sensitivity_dialog.table.setColumnWidth(nombres_columnas.index("Distribution parameters"), 200)
            
        #Añadir filas
        def add_element(columna,texto):
            item = QTableWidgetItem(texto)
            self.sensitivity_dialog.table.setItem(numero_filas, columna, item)
            item.setTextAlignment(Qt.AlignCenter)
        
        #Primero la información de los lineEdits
        numero_filas = self.sensitivity_dialog.table.rowCount()
        self.sensitivity_dialog.table.setRowCount(numero_filas + 1)
        #Add parameter
        add_element(0,self.sensitivity_dialog.parameter.text())
        #Add distribution
        distribution = [self.sensitivity_dialog.distributions.itemText(i) for i in range(self.sensitivity_dialog.distributions.count())][self.sensitivity_dialog.distributions.currentIndex()]
        add_element(1,distribution)
        #Add distribution parameters
        if distribution=="Uniform" or distribution=="Logaritmic uniform":
            add_element(2,f"min:{self.sensitivity_dialog.first.text()},max:{self.sensitivity_dialog.second.text()}")
        elif distribution == "Triangular":
            add_element(2,f"min:{self.sensitivity_dialog.first.text()},max:{self.sensitivity_dialog.second.text()},peak:{self.sensitivity_dialog.third.text()}")
        elif distribution == "Normal" or distribution == "Lognormal":
            add_element(2,f"mean:{self.sensitivity_dialog.first.text()},stdv:{self.sensitivity_dialog.second.text()}")
        elif distribution == "Normal truncated":
            add_element(2,f"min:{self.sensitivity_dialog.first.text()},max:{self.sensitivity_dialog.second.text()},mean:{self.sensitivity_dialog.third.text()},stdv:{self.sensitivity_dialog.fourth.text()}")
        #Add row
        add_element(3,self.sensitivity_dialog.row.text())
        
        #Update number of samples
        self.change_sensitivity_metod
    
    
    def add_calibration_table(self):
        #Metod to add calibration analysis parameters to table
        if self.dlg_calibration.table.columnCount() == 0:
            #Añadir columnas
            nombres_columnas = ["Parameter","Minimum","Maximum","Row"]
            self.dlg_calibration.table.setColumnCount(len(nombres_columnas))
            self.dlg_calibration.table.setHorizontalHeaderLabels(nombres_columnas)
            #Cambiar el ancho de las columnas
            self.dlg_calibration.table.setColumnWidth(nombres_columnas.index("Parameter"), 180)
            
        #Añadir filas
        def add_element(columna,texto):
            item = QTableWidgetItem(texto)
            self.dlg_calibration.table.setItem(numero_filas, columna, item)
            item.setTextAlignment(Qt.AlignCenter)
        
        #Primero la información de los lineEdits
        numero_filas = self.dlg_calibration.table.rowCount()
        self.dlg_calibration.table.setRowCount(numero_filas + 1)
        #Add parameter
        add_element(0,self.dlg_calibration.parameter.text())
        #Add minimum
        add_element(1,self.dlg_calibration.first.text())
        #Add maximum
        add_element(2,self.dlg_calibration.second.text())
        #Add row
        add_element(3,self.dlg_calibration.row.text())

    
    
    def delete_sensitivity_table(self):
        #Metod to delete sensitivity analysis parameters to table
        numero_filas = self.sensitivity_dialog.table.rowCount()
        if numero_filas > 0:
            self.sensitivity_dialog.table.removeRow(numero_filas - 1)
        if numero_filas == 1:
            self.sensitivity_dialog.table.setColumnCount(0)
        
        #Update number of samples
        self.change_sensitivity_metod()
    
    def delete_calibration_table(self):
        #Metod to delete sensitivity analysis parameters to table
        numero_filas = self.dlg_calibration.table.rowCount()
        if numero_filas > 0:
            self.dlg_calibration.table.removeRow(numero_filas - 1)
        if numero_filas == 1:
            self.dlg_calibration.table.setColumnCount(0)
        
        #Update number of samples
        self.change_sensitivity_metod()
    
    def add_parameter_label(self,nombre):
        #Metod to add the parameter to the lineEdit
        self.sensitivity_dialog.parameter.setText(str(nombre))
    
    def add_parameter_label_calibration(self,nombre):
        #Metod to add the parameter to the lineEdit
        self.dlg_calibration.parameter.setText(str(nombre))
    
    def create_dictionary_sensitivity_analysis(self):
        """Method to create the dictionary of the sensitivity analysis"""
        #Functions to convert user specified inputs into inputs that SALib can read
        def distribution_parameters_fun(row):
            if str(self.sensitivity_dialog.table.item(row, 1).text()) == "Uniform":
                distribution = "unif"
                texto = str(self.sensitivity_dialog.table.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.sensitivity_dialog.table.item(row, 1).text()) == "Logaritmic uniform":
                distribution = "logunif"
                texto = str(self.sensitivity_dialog.table.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.sensitivity_dialog.table.item(row, 1).text()) == "Triangular":
                distribution = "triang"
                texto = str(self.sensitivity_dialog.table.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.sensitivity_dialog.table.item(row, 1).text()) == "Normal":
                distribution = "norm"
                texto = str(self.sensitivity_dialog.table.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.sensitivity_dialog.table.item(row, 1).text()) == "Normal truncated":
                distribution = "truncnorm"
                texto = str(self.sensitivity_dialog.table.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            elif str(self.sensitivity_dialog.table.item(row, 1).text()) == "Lognormal":
                distribution = "lognorm"
                texto = str(self.sensitivity_dialog.table.item(row, 2).text())
                parameters = [float(x.split(":")[-1]) for x in texto.split(",")]
            return distribution, parameters
            
            
        #Diccionario nombre en el diálogo - [parametros del análisis de sensibilidad]
        self.dic_data = {}
        for i in range(self.sensitivity_dialog.table.rowCount()):
            #Diccionario [Parametro] = (Distribucion, Parametros, Row)
            name = self.sensitivity_dialog.table.item(i, 0).text()
            #Obtain name of distribution and parameters
            dis,param = distribution_parameters_fun(i)
            if name in self.dic_data:name = name+"__1"
            self.dic_data[name] = [dis,param,self.sensitivity_dialog.table.item(i, 3).text()]
        
        #Se crean las muestras
        #Problema
        self.problem = {'num_vars': len(self.dic_data),'names': list(self.dic_data.keys()),'bounds': [x[1] for x in self.dic_data.values()],"dists":[x[0] for x in self.dic_data.values()]}
        #Muestras
        if self.sensitivity_dialog.sobol.isChecked():
            self.param_values = saltelli.sample(self.problem, int(self.sensitivity_dialog.trajectories.text()))
        elif self.sensitivity_dialog.morris.isChecked():
            self.param_values = sample_morris(self.problem, int(self.sensitivity_dialog.trajectories.text()))
    
    
    def create_dictionary_calibration(self):
        """Method to create the dictionary of the calibration"""
        #Diccionario nombre en el diálogo - [parametros del análisis de sensibilidad]
        self.dic_data = {}
        for i in range(self.dlg_calibration.table.rowCount()):
            #Diccionario [Parametro] = (Minimo, Maximo, Row)
            name = self.dlg_calibration.table.item(i, 0).text()
            minimum = self.dlg_calibration.table.item(i, 1).text()
            maximum = self.dlg_calibration.table.item(i, 2).text()
            row = self.dlg_calibration.table.item(i, 3).text()
            if name in self.dic_data:name = name+"__1"
            self.dic_data[name] = [minimum,maximum,row]
        
        
    
    def move_files_to_working_directory_sensitivity_analysis(self,information):
        """Method to move the files from the selected project to the working directory"""
        #Se abre el archivo
        if information == "Sensitivity_analysis":
            selected_project = self.sensitivity_dialog.project_sensitivity.currentText()
        elif information == "Calibration":
            selected_project = self.dlg_calibration.project_calibration.currentText()
        
        #Move all the folders to the new folder
        for core in range(1,self.number_cores+1):
            origen = Path(self.carpeta_guardar_proyectos +"\\"+selected_project)
            destino = Path(self.dlg.project.text()+"\\"+selected_project+f"\\{information}\\Core_{core}")

            destino.mkdir(parents=True, exist_ok=True)
            
            for carpeta in origen.iterdir() :
                if carpeta.is_dir() and carpeta.name != "Sensitivity_analysis" and carpeta.name != "Calibration":
                    try:
                        shutil.copytree(
                            carpeta,
                            destino / carpeta.name,
                            dirs_exist_ok=True
                        )
                    except Exception as e:
                        self.end_execution = 1
                        self.warning_message(str(e))
                        return
        
            #Create also the executables
            #Executable of TopAGNPS
            shutil.copyfile(str(Path(self.executable_directory+"/EjecutarTopagnps.bat")), str(Path(self.executable_directory+"/"+f"EjecutarTopagnps_{core}.bat")))
            f = open(str(Path(self.executable_directory+"/"+f"EjecutarTopagnps_{core}.bat")),"w+")
            linea_uno = "CD {}".format(self.direccion_sensitivity+f"\\Core_{core}\\Preprocessing_inputs")
            linea_dos = r"CALL {}\TopAGNPS_v6.00.a.025_release_64-bit.exe".format(self.executable_directory)
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.close()
            #Executable of AnnAGNPS
            shutil.copyfile(str(Path(self.executable_directory+"/EjecutarAnnAGNPS.bat")), str(Path(self.executable_directory+"/"+f"EjecutarAnnAGNPS_{core}.bat")))
            f = open(str(Path(self.executable_directory+"/"+f"EjecutarAnnAGNPS_{core}.bat")),"w+")
            linea_uno = "CD {}".format(self.direccion_sensitivity+f"\\Core_{core}\\Processing_inputs")
            linea_dos = r"CALL {}\AnnAGNPS_v6.00.r.058_release_64-bit.exe".format(self.executable_directory)
            f.write("{} \n".format(linea_uno))
            f.write("{} \n".format(linea_dos))
            f.close()
            
            
    
    def modify_input_sensitivity_match_output(self,information):
        """Method to change the input files so that the output appears"""
        #Method to crete the needed files to have the desired outputs
        def modify_input(name_master,column,new_columns,name_new_file):
            master_file = self.direccion_sensitivity+f"\\Core_{core}"+r"\Processing_inputs\annagnps_master.csv"
            project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")

            if name_master in project_df.iloc[:,0].values:
                file = Path(self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]==name_master].iloc[0,1])
                data = pd.read_csv(file,encoding = "ISO-8859-1",delimiter=",")
                # Eliminar espacios al inicio y final de los nombres de columnas
                data.columns = data.columns.str.strip()
                data[column].iloc[0] = "T"
                data.to_csv(file, index=False, float_format='%.5f')
                
            else:
                columns = new_columns
                data = pd.DataFrame(columns=columns, data=[[""] * len(columns)])
                data[column].iloc[0] = "T"
                nombre = name_new_file
                file = Path(self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_inputs"+"\\simulation\\"+f"{nombre}.csv")
                data.to_csv(file, index=False, float_format='%.5f')
                project_df.loc[len(project_df)] = [name_master, f".\simulation\{nombre}.csv"]
                project_df.to_csv(master_file, index=False, float_format='%.5f')
        
        #Method to add th input code to the global factors
        def select_input_code():
            master_file = self.direccion_sensitivity+f"\\Core_{core}"+r"\Processing_inputs\annagnps_master.csv"
            project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")

            file = Path(self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]=="AnnAGNPS ID"].iloc[0,1])
            data = pd.read_csv(file,encoding = "ISO-8859-1",delimiter=",")
            input_code = data["Input_Units"].iloc[0]
            
            #Ahora se mete en el global factors
            file = Path(self.direccion_sensitivity+f"\\Core_{core}"+"\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]=="Global IDs Factors and Flags Data"].iloc[0,1])
            data = pd.read_csv(file,encoding = "ISO-8859-1",delimiter=",")
            try:
                int(input_code)
                data["Input_Units_Code"].iloc[0] = input_code
            except:
                data["Input_Units_Code"].iloc[0] = str(0)
                

            data.to_csv(file, index=False,float_format='%.5f')
        
        if information == "Sensitivity_analysis":
            for core in range(1,self.number_cores+1):
            
                if self.sensitivity_dialog.runoff.isChecked(): 
                    columns = ["Cell_Components","Conversion_Units","Sht/Rill_Eros_Sed_Yld","Feedlots","Insitu_N_Inorg","Insitu_N_Org","Insitu_Residue","Insitu_OC","Insitu_P_Inorg","Insitu_P_Org","Insitu_Soil_Moist_Daily","Irrigation","Pesticide_App","Pesticide_Insitu","Gully","Reach_Acc_Mass","Reach_Acc_Ratio","LS_Yld_All_Srcs","Reach_Ld_Nutr","Reserved","Reach_Ld_Sed","Reach_Ld_Wtr","Impound_Routing_A","Reserved","Reach_Routing_Pest","Reach_Routing","Reach_Routing_Wtr","Runoff_Curve_Num","Schd_Oprs","Soil_Part_Distrib","Pond_Release/Yield","Winter_Thermal","Reserved","USLE_Params","Baseflow","Insitu_Soil_Moist_Wsh d_Sum","Wetland_Effects","Pot_ET_Adjust","LS_Rnof_All_Srcs","Riparian_Buffers"]
                    modify_input("Output Options - SIM","Insitu_Soil_Moist_Daily",columns,"out_sim")
                
                if self.sensitivity_dialog.total_erosion.isChecked() or self.sensitivity_dialog.gully.isChecked() or self.sensitivity_dialog.sheet.isChecked() or self.sensitivity_dialog.pond.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_Sed_Yld_Mass",columns,"out_ev")
                    
                    
                if self.sensitivity_dialog.ephemeral.isChecked():
                    #poner aqui que se ponga el input units code de AnnAGNPSID, y que si en AnnAGNPSID no hay entonces se pone el 0 qu es el por defecto
                    columns = ["Hdct_Detachment_Coef_a", "Hdct_Detachment_Exp_Coef_b", "Urban_Repair_Month", "Urban_Repair_Day", "Urban_Repair_Year", "Cropland_Repair_Month", "Cropland_Repair_Day", "Cropland_Repair_Year", "Forest_Repair_Month", "Forest_Repair_Day", "Forest_Repair_Year", "Pasture_Repair_Month", "Pasture_Repair_Day", "Pasture_Repair_Year", "Rangeland_Repair_Month", "Rangeland_Repair_Day", "Rangeland_Repair_Year", "Hdct_Erodibility_Coef_a", "Hdct_Erodibility_Exp_Coef_b", "Width_Nachtergaele", "Width_Hydraulic_Geometry", "Width_Non-submerging_Tailwater", "Width_Woodwards_Equilibrium", "Width_Woodwards_Ultimate", "Width_Wells_Eq.9", "Erosion_Vrfy", "Hydrograph_Vrfy", "Nickpoint_Vrfy", "Repair_Dates_Vrfy", "Sed_Yield_to_Gully_Mouth_Vrfy", "Sed_Yield_to_Rcvg_Reach_Vrfy", "Min_Interception_Evaporation", "Max_Interception_Evaporation", "Detention_Coef_a", "Detention_Coef_b", "RCN_Convergence_Tolerance", "RCN_Max_Iterations", "Avbl_Soil_Moist_Ratio_AMC_II", "Max_Avbl_Sed_Conc_for_Sht_Flw", "Max_Avbl_Sed_Conc_for_Conc_Flw", "AA_Unit_Area_Baseflow", "RCN_Calib_Only", "Calculate_Baseflow", "FAO_ET_Enhancement", "Basal_Crop_Coef_Climate_Adjust", "Wshd_Storm_Type_ID", "Dflt_Geology_ID", "Dflt_Hydraulic_Geom_ID", "Dflt_Init_Soil_Conditions_ID", "Dflt_Crop_RCN_ID", "Dflt_Non-Crop_RCN_ID", "Width_Wells_Eq.8", "Width_Reserved_i", "Width_Reserved_j", "Width_Reserved_k", "Critical_Shear_Stress", "RUSLE2_Flag", "Dflt_RUSLE2_ID", "Input_Units_Code"]
                    modify_input("Global IDs Factors and Flags Data","Erosion_Vrfy",columns,"global_factors")
                    select_input_code()
                    columns = ["Cell_Components","Conversion_Units","Sht/Rill_Eros_Sed_Yld","Feedlots","Insitu_N_Inorg","Insitu_N_Org","Insitu_Residue","Insitu_OC","Insitu_P_Inorg","Insitu_P_Org","Insitu_Soil_Moist_Daily","Irrigation","Pesticide_App","Pesticide_Insitu","Gully","Reach_Acc_Mass","Reach_Acc_Ratio","LS_Yld_All_Srcs","Reach_Ld_Nutr","Reserved","Reach_Ld_Sed","Reach_Ld_Wtr","Impound_Routing_A","Reserved","Reach_Routing_Pest","Reach_Routing","Reach_Routing_Wtr","Runoff_Curve_Num","Schd_Oprs","Soil_Part_Distrib","Pond_Release/Yield","Winter_Thermal","Reserved","USLE_Params","Baseflow","Insitu_Soil_Moist_Wsh d_Sum","Wetland_Effects","Pot_ET_Adjust","LS_Rnof_All_Srcs","Riparian_Buffers"]
                    modify_input("Output Options - SIM","Gully",columns,"out_sim")
                    
                if self.sensitivity_dialog.nitrogen.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_N_Yld_Mass",columns,"out_ev")
                
                
                if self.sensitivity_dialog.organic.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_OC_Yld_Mass",columns,"out_ev")
                
                if self.sensitivity_dialog.phosphorus.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_P_Yld_Mass",columns,"out_ev")
        
        elif information == "Calibration":
            for core in range(1,self.number_cores+1):
            
                if self.dlg_calibration.runoff.isChecked(): 
                    columns = ["CCHE1D", "CONCEPTS_XML", "Gaging_Station_Hyd", "REMM", "Gaging_Station_Evt"]
                    modify_input("Output Options - TBL","Gaging_Station_Hyd",columns,"out_tbl")
                
                elif self.dlg_calibration.total_erosion.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_Sed_Yld_Mass",columns,"out_ev")
                    
                    
                elif self.dlg_calibration.nitrogen.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_N_Yld_Mass",columns,"out_ev")
                
                
                elif self.dlg_calibration.organic.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_OC_Yld_Mass",columns,"out_ev")
                
                elif self.dlg_calibration.phosphorus.isChecked(): 
                    columns = ["Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_N_Ld_Mass","EV_N_Ld_Ratio","EV_N_Ld_UA","EV_N_Yld_Mass","EV_N_Yld_Ratio","EV_N_Yld_UA","EV_OC_Ld_Mass","EV_OC_Ld_Ratio","EV_OC_Ld_UA","EV_OC_Yld_Mass","EV_OC_Yld_Ratio","EV_OC_Yld_UA","Reserved","Reserved","Reserved","Reserved","Reserved","Reserved","EV_P_Ld_Mass","EV_P_Ld_Ratio","EV_P_Ld_UA","EV_P_Yld_Mass","EV_P_Yld_Ratio","EV_P_Yld_UA","Reserved","Reserved","Reserved","EV_Sed_Eros_Mass","EV_Sed_Eros_Ratio","EV_Sed_Eros_UA","EV_Sed_Ld_Mass","EV_Sed_Ld_Ratio","EV_Sed_Ld_UA","EV_Sed_Yld_Mass","EV_Sed_Yld_Ratio","EV_Sed_Yld_UA","EV_Wtr_Ld_Mass","EV_Wtr_Ld_Ratio","EV_Wtr_Ld_UA","EV_Wtr_Yld_Mass","EV_Wtr_Yld_Ratio","EV_Wtr_Yld_UA","EV_LS_Rnof_All_Srcs","EV_LS_Yld_All_Srcs","EV_Gullies_Erosion"]
                    modify_input("Output Options - EV","EV_P_Yld_Mass",columns,"out_ev")
        
    
    def run_calibration(self): 
        #Metod to run sensitiviy analysis
        self.end_execution = 0
        #If there is not working directory selected then error
        if self.dlg.project.text()=="":
            self.warning_message("Please select a working directory where the files are going to be loaded")
            return
        
        #Check if the period of the observed is the same as the simulation
        if self.check_period_match_observed_simulated_calibration():
            self.warning_message("The observed data cover a period that is not simulated. \nPlease make sure that the observed period falls within the simulation period (Simulation period data).")
            return
        
        #Close dialogs
        self.dlg_calibration.close()
        self.dlg.close()

        #Start with the progress bar
        self.progress_metod("Calibration",start = True)
        
        #Create the dictionary with the input data and the parameter values
        self.create_dictionary_calibration()        
        
        #Obtain the number of cores to work with
        self.number_cores = QThreadPool.globalInstance().maxThreadCount() - 1
        
        #Obtener la direccoin de los raster ahora que están en la carpeta de "Sensitivity_analysis"
        self.declare_rasters_sensitivity_analysis("Calibration")
        
        #Move the files from the save project to working directory + name of the project + "Sensitivity_analysis"
        self.progress_dialog.setLabelText("Moving files to the working directory...")
        self.move_files_to_working_directory_sensitivity_analysis("Calibration")
        if self.end_execution:
            return
        
        
        #Modifiy the inputs so that the required output are displayed
        self.modify_input_sensitivity_match_output("Calibration")
        
        
        #Results are obtained
        self.resultados = []
        self.numero_ejecucion = 0
        self.end_execution = False
        
        
        #Check if preprocessing is going to be executed
        self.execute_preprocessing_calibration = False
        for i in self.dic_data.keys():
            if self.dic_name_column[i][0]=="Spatial":
                self.execute_preprocessing_calibration = True
        
        
        #We do the sensitivity analysis
        self.manager = QgsApplication.instance().taskManager()
        self.carpetas_libres = list(range(1,self.number_cores+1))  # IDs de tus carpetas
        try:
            self.calibration_maximum_executions = int(self.dlg_calibration.trajectories.text())
            self.tareas_pendientes = list(range(self.calibration_maximum_executions))
        except:
            self.warning_message("Please select a number for the maximum iterations")
            return
        self.terminadas = 0
        self.tareas_activas = []
        
        #Obtener la cantidad de tareas que se ve a hacer en cada ronda
        self.tareas_por_ronda = self.number_cores-1
        self.tareas_pendientes_ronda = list(range(self.tareas_por_ronda))
        
        #Do the calibration until the tareas pendientes is reached
        espacio = [(float(x[0]),float(x[1])) for x in self.dic_data.values()]
        self.opt = Optimizer(dimensions=espacio, base_estimator="GP")
        self.counter_calibration = 0
        self.counter_calibration_round = 0
        self.resultados_outputs_calibration = []
        self.proximos_inputs = self.opt.ask(n_points=self.tareas_por_ronda)
        self.lanzar_siguiente_calibration()
    
            
    def run_sensitivity_analysis(self): 
        #Metod to run sensitiviy analysis
        self.end_execution = 0
        #If there is not working directory selected then error
        if self.dlg.project.text()=="":
            self.warning_message("Please select a working directory where the files are going to be loaded")
            return
        
        #Close dialogs
        self.sensitivity_dialog.close()
        self.dlg.close()

        #Start with the progress bar
        self.progress_metod("Sensitivity",start = True)
        
        
        #Create the dictionary with the input data and the parameter values
        self.create_dictionary_sensitivity_analysis()        
        
        #Obtain the number of cores to work with
        self.number_cores = QThreadPool.globalInstance().maxThreadCount() - 1
        
        #Obtener la direccoin de los raster ahora que están en la carpeta de "Sensitivity_analysis"
        self.declare_rasters_sensitivity_analysis("Sensitivity_analysis")
        
        #Move the files from the save project to working directory + name of the project + "Sensitivity_analysis"
        self.progress_dialog.setLabelText("Moving files to the working directory...")
        self.move_files_to_working_directory_sensitivity_analysis("Sensitivity_analysis")
        if self.end_execution:
            return
        
        
        #Modifiy the inputs so that the required output are displayed
        self.modify_input_sensitivity_match_output("Sensitivity_analysis")
        
        
        #Si se ha escogido la opción de "Pixel Size" se obtienen todos los DEMs con todos los tamaños de píxeles
        if "Pixel Size" in list(self.dic_data.keys()):
            self.resample_rasters_sensitivity()
        else: #si no se hace resample entonces no se crean variables como self.nombre_mdt_sensitivity que lo paso a la paralelización del análisis de sensibilidad, por eso los creo aquí
            self.nombre_mdt_sensitivity ="nan"
            self.extension_mdt_sensitivity ="nan"
            self.nombre_buffer_sensitivity = "nan"
            self.extension_buffer_sensitivity ="nan"
            self.nombre_vegetation_sensitivity ="nan"
            self.extension_vegetation_sensitivity ="nan"
            
        #Results are obtained
        self.resultados = []
        self.numero_ejecucion = 0
        self.end_execution = False
        
        
        #Check if preprocessing is going to be executed
        self.execute_preprocessing_sensitivity = False
        for i in self.dic_data.keys():
            if self.dic_name_column[i][0]=="Spatial":
                self.execute_preprocessing_sensitivity = True
        
        
        #We do the sensitivity analysis
        self.manager = QgsApplication.instance().taskManager()
        self.carpetas_libres = list(range(1,self.number_cores+1))  # IDs de tus carpetas
        self.tareas_pendientes = list(range(len(self.param_values)))
        self.terminadas = 0
        self.tareas_activas = []
        self.lanzar_siguiente_sensitivity()
        
        
    
    def lanzar_siguiente_sensitivity(self):
        """Method to run next execution in the parallelization of the sensitivity analysis"""
        
        if not self.tareas_pendientes:
            return
        
        # Mientras haya tareas por hacer y carpetas vacías...
        while self.tareas_pendientes and self.carpetas_libres:
            
            n_tarea = self.tareas_pendientes.pop(0)
            id_carpeta = self.carpetas_libres.pop(0) # Reservamos la carpeta
            task = Sensitivity_Parallelization(n_tarea, id_carpeta,self.execute_preprocessing_sensitivity,self.direccion_sensitivity,
                self.dic_data,self.param_values,self.executable_directory,self.plugin_dir,self.dic_name_column,self.nombre_mdt_sensitivity,
                self.extension_mdt_sensitivity,self.fichero_buf_sensitivity,self.nombre_buffer_sensitivity,self.extension_buffer_sensitivity,
                self.fichero_veg_sensitivity,self.nombre_vegetation_sensitivity,self.extension_vegetation_sensitivity,self.inputs,self.epsg_sensitivity,
                self.unique_soil_sensitivity, self.fichero_soil_sensitivity,self.column_soil_sensitivity,self.unique_use_sensitivity,self.fichero_manag_sensitivity,
                self.column_use_sensitivity,self.project_df)
            
            self.tareas_activas.append(task)
            
            # Al finalizar, liberamos la carpeta y lanzamos la siguiente
            task.taskCompleted.connect(lambda t=task, f=id_carpeta,n = n_tarea: self.finalizar_tarea_sensitivity(t, f, n))
            # Esto es por si hay error
            task.taskTerminated.connect(lambda t=task, f=id_carpeta,n = n_tarea: self.finalizar_tarea_sensitivity(t, f, n))
            self.manager.addTask(task)
    
    
    def finalizar_tarea_sensitivity(self,task, id_carpeta,n):
        """Method that will be executed after each execution in AnnAGNPS in the parallelization of the sensitivity analysis"""
    
        # IMPORTANT: Remove from active list immediately
        if task in self.tareas_activas:
            self.tareas_activas.remove(task)
            
        # Check if the task failed or was canceled
        if task.status() != QgsTask.Complete:
            # Check if we already cleared the queue (to avoid multiple popups)
            if len(self.tareas_pendientes) > 0:
                self.stop_sensitivity_execution(task)
            return # Stop this specific execution branch here
        
        # --- Normal Success Logic ---
        # We save the result
        resultado = self.save_result(id_carpeta, n)
        self.resultados.append(resultado)
        
        
        self.terminadas += 1
        # Return folder to pool
        self.carpetas_libres.append(id_carpeta)
        
        
        if self.terminadas >= len(self.param_values):
            #Se ponen los resultados en un dataframe, se guarda y se calculan los índices de sensibilidad
            self.run_sensitivity_analysis_two()
            
        else:
            # Only launch next if the queue hasn't been emptied by an error
            if self.tareas_pendientes:
                self.lanzar_siguiente_sensitivity()
    
    def finalizar_tarea_calibration(self,task, id_carpeta,n,proximos_inputs,counter_round):
        """Method that will be executed after each execution in AnnAGNPS in the parallelization of the calibration"""
    
        # IMPORTANT: Remove from active list immediately
        if task in self.tareas_activas:
            self.tareas_activas.remove(task)
            
        # Check if the task failed or was canceled
        if task.status() != QgsTask.Complete:
            # Check if we already cleared the queue (to avoid multiple popups)
            if len(self.tareas_pendientes) > 0:
                self.stop_calibration_execution(task)
            return # Stop this specific execution branch here
        
        # --- Normal Success Logic ---
        # We save the result
        resultado = self.obtain_nash_calibration(id_carpeta,proximos_inputs,counter_round)
        self.resultados.append(resultado)
        
        self.counter_calibration +=1
        self.counter_calibration_round +=1
        
        # Return folder to pool
        self.carpetas_libres.append(id_carpeta)
        
        
        if self.counter_calibration >= self.calibration_maximum_executions:
            #Se ponen los resultados en un dataframe, se guarda y se calculan los índices de sensibilidad
            self.run_calibration_two()
        
        elif self.counter_calibration_round >= self.tareas_por_ronda:
            self.counter_calibration_round = 0
            self.lanzar_siguiente_calibration()
            self.opt.tell(self.proximos_inputs, self.resultados_outputs_calibration)
            self.proximos_inputs = self.opt.ask(n_points=self.tareas_por_ronda)
            self.resultados_outputs_calibration = []
            
        
        else:
            # Only launch next if the queue hasn't been emptied by an error
            if self.tareas_pendientes:
                self.lanzar_siguiente_calibration()
    
    def check_period_match_observed_simulated_calibration(self):
        """Method to check if observed and simulated periods are the same in the calibration"""
        #Obtain observed date
        file_path = self.dlg_calibration_inputs.lineEdit.text()
        df_observed = pd.read_csv(file_path, sep=',', header=None)
        df_observed.columns = ['date', 'value']


        df_observed['date'] = pd.to_datetime(df_observed['date'], format='%d/%m/%Y', errors='coerce')
        df_observed['value'] = pd.to_numeric(df_observed['value'], errors='coerce')
        df_observed = df_observed.dropna().sort_values('date')
        
        start_date_observed = df_observed['date'].min()
        end_date_observed = df_observed['date'].max()
        
        #Obtain simulated date
        master_file = self.carpeta_guardar_proyectos+f"\\{self.dlg_calibration.project_calibration.currentText()}\\" +r"\Processing_inputs\annagnps_master.csv"
        project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")

        file_path = self.carpeta_guardar_proyectos+f"\\{self.dlg_calibration.project_calibration.currentText()}\\" +r"\\Processing_inputs\\"+project_df[project_df.iloc[:,0]=="Simulation Period Data"].iloc[0,1]
        df_observed = pd.read_csv(file_path, sep=',')



        start_date_simulated = pd.to_datetime({'year':[df_observed["Simulation_Begin_Year"].iloc[0]], 
                                    'month':[df_observed["Simulation_Begin_Month"].iloc[0]], 
                                    'day':[df_observed["Simulation_Begin_Day"].iloc[0]]})[0]

        end_date_simulated = pd.to_datetime({'year':[df_observed["Simulation_End_Year"].iloc[0]], 
                                    'month':[df_observed["Simulation_End_Month"].iloc[0]], 
                                    'day':[df_observed["Simulation_End_Day"].iloc[0]]})[0]
        
        if start_date_observed<start_date_simulated or end_date_observed>end_date_simulated:
            return True
        
        return False

        
        
    
    
    def obtain_nash_calibration(self,id_carpeta,proximos_inputs,counter_round):
        """Method to obtain the objective funciotn value in the calibration"""
        #Put the values of the inputs
        data_to_save = {}
        
        #We add input files
        for k,i in enumerate(self.dic_data.keys()):  
            data_to_save[i.replace("\n", " ")] = proximos_inputs[counter_round][k]
        
        
        #Obtain df of observed
        file_path = self.dlg_calibration_inputs.lineEdit.text()
        df_observed = pd.read_csv(file_path, sep=',', header=None)
        df_observed.columns = ['date', 'value']


        df_observed['date'] = pd.to_datetime(df_observed['date'], format='%d/%m/%Y', errors='coerce')
        df_observed['value'] = pd.to_numeric(df_observed['value'], errors='coerce')
        df_observed = df_observed.dropna().sort_values('date')
        
        
        #Obtain df of simulated
        fichero= self.direccion_sensitivity+f"\\Core_{id_carpeta}"+"\\Processing_outputs\AnnAGNPS_TBL_Gaging_Station_Data_Hyd.csv"
        first_column = "Gregorian Day"



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
           
        df_simulated = pd.DataFrame(columns = lista[0],data = lista[1:])
        df_simulated = df_simulated[df_simulated["Reach ID"]=="OUTLET"]
        df_simulated['date'] = pd.to_datetime(df_simulated[['Year', 'Month', 'Day']])
        # Encontrar la columna que contiene "Total Streamflow"
        total_col = [col for col in df_simulated.columns if "Total Streamflow" in col][0]
        # Seleccionar solo la columna 'Date' y la columna de Total Streamflow
        df_simulated = df_simulated[['date', total_col]]
        df_simulated[total_col] = df_simulated[total_col].astype(float)
        df_simulated = df_simulated.rename(columns={total_col: 'value'})



        #Calculate nash
        df_merged = pd.merge(df_observed, df_simulated, on='date', suffixes=('_observed', '_simulated'))
        obs = df_merged['value_observed'].values
        sim = df_merged['value_simulated'].values

        # Calcular NSE
        nse = 1 - np.sum((obs - sim)**2) / np.sum((obs - np.mean(obs))**2)
        
        self.resultados_outputs_calibration.append(-nse)
        
        
        data_to_save["Nash_Sutcliffe"]=nse
        
        #Save best result
        if len(self.resultados)==0:
            self.best_result_calibration = [df_merged,data_to_save]
        
        elif nse>=max(d["Nash_Sutcliffe"] for d in self.resultados):
            self.best_result_calibration = [df_merged,data_to_save]
        
        return data_to_save
        
    
    def stop_sensitivity_execution(self,task):
        """Método para detener el análisis de sensibilidad de forma segura"""
        self.tareas_pendientes = []  # Clear the queue
        
        # Use a copy [:] to iterate safely
        for t in self.tareas_activas[:]:
            try:
                # We only cancel tasks that are still alive and are NOT the failed one
                if t and t != task:
                    t.cancel()
            except (RuntimeError, ReferenceError):
                pass
                
        self.tareas_activas = [] 
        
        # Try to build the error message safely
        try:
            msg = f"Analysis stopped in task {task.n}. Reason: {task.error_msg}"
        except (RuntimeError, ReferenceError, AttributeError):
            msg = "Sensitivity analysis stopped due to an unexpected error."

        # Show the warning in English
        self.warning_message(msg)
        
        #Close progress bar
        self.progress_dialog.close()
    
    
    def stop_calibration_execution(self,task):
        """Método para detener el análisis de sensibilidad de forma segura"""
        self.tareas_pendientes = []  # Clear the queue
        
        # Use a copy [:] to iterate safely
        for t in self.tareas_activas[:]:
            try:
                # We only cancel tasks that are still alive and are NOT the failed one
                if t and t != task:
                    t.cancel()
            except (RuntimeError, ReferenceError):
                pass
                
        self.tareas_activas = [] 
        
        # Try to build the error message safely
        try:
            msg = f"Analysis stopped in task {task.n}. Reason: {task.error_msg}"
        except (RuntimeError, ReferenceError, AttributeError):
            msg = "Calibration analysis stopped due to an unexpected error."

        # Show the warning in English
        self.warning_message(msg)
        
        #Close progress bar
        self.progress_dialog.close()
    
    
    def lanzar_siguiente_calibration(self):
        """Method to run next execution in the parallelization of the calibration"""
        
        if not self.tareas_pendientes:
            return
        
        # Mientras haya tareas por hacer y carpetas vacías...
        while self.tareas_pendientes and self.carpetas_libres:
            
            n_tarea = self.tareas_pendientes.pop(0)
            id_carpeta = self.carpetas_libres.pop(0) # Reservamos la carpeta
            task = Calibration_Parallelization(n_tarea, id_carpeta,self.execute_preprocessing_calibration,self.direccion_sensitivity,
                self.dic_data,self.proximos_inputs,self.executable_directory,self.plugin_dir,self.dic_name_column,
                self.inputs,self.epsg_sensitivity,
                self.unique_soil_sensitivity, self.fichero_soil_sensitivity,self.column_soil_sensitivity,self.unique_use_sensitivity,self.fichero_manag_sensitivity,
                self.column_use_sensitivity,self.project_df,self.counter_calibration_round)
            
            self.tareas_activas.append(task)
            
            # Al finalizar, liberamos la carpeta y lanzamos la siguiente
            task.taskCompleted.connect(lambda t=task, f=id_carpeta,n = n_tarea: self.finalizar_tarea_calibration(t, f, n,self.proximos_inputs,self.counter_calibration_round))
            # Esto es por si hay error
            task.taskTerminated.connect(lambda t=task, f=id_carpeta,n = n_tarea: self.finalizar_tarea_calibration(t, f, n,self.proximos_inputs,self.counter_calibration_round))
            self.manager.addTask(task)
    
    
    
    def save_result(self,core,n):
        #Metod to save the results of the sensitivity analysis
        data_to_save = {}
        
        #We add input files
        for k,i in enumerate(self.dic_data.keys()):  
            data_to_save[i.replace("\n", " ")] = self.param_values[n][k]
        
        #Runoff
        if self.sensitivity_dialog.runoff.isChecked():
            #Se importan los datos
            try:
                df = self.import_df("Runoff",core,sensitivity=True)
            except:
                self.end_execution =True
                return
            #Esto se hace porque la escorrentía de la cuenca es la media ponderada con el área de las escorrentías de las celdas
            try:
                df['Runoff_Ponderado'] = df['Runoff'] * df['Drainage']
                result = df.groupby('Fecha').agg({'Runoff_Ponderado': 'sum', 'Drainage': 'sum'}).reset_index()
            except:
                self.end_execution =True
                self.warning_message("AnnAGNPS_SIM_Insitu_Soil_Moisture output not found. \nInsitu_Soil_Moisture_Daily column in OUTPUT OPTIONS DATA -SIM file must be set to T ")
                return
            result['Runoff'] = result['Runoff_Ponderado'] / result['Drainage']
            df_graph = result[['Fecha', 'Runoff']]
            df_graph.set_index('Fecha', inplace=True)
            data_to_save["Total runoff (mm)"] = df_graph["Runoff"].sum()

        #Total erosion
        if self.sensitivity_dialog.total_erosion.isChecked():
            df = self.import_df("Subtotal",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Sediment_yield_(mass) output not found. \nEV_Sed_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
                
            data_to_save["Total erosion (Mg)"] = df_graph.sum()       
            
        #Gully erosion
        if self.sensitivity_dialog.gully.isChecked():
            df = self.import_df("Gully",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Sediment_yield_(mass) output not found. \nEV_Sed_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
            data_to_save["Gully erosion (Mg)"] = df_graph.sum()    
            
        #Ephemeral gully
        r'''if self.sensitivity_dialog.ephemeral.isChecked():
            fichero = self.direccion_sensitivity+"\\Preprocessing_outputs\\"+"AnnAGNPS_SIM_Ephemeral_Gully_Erosion.csv"
            try:
                file = open(fichero)
            except:
                self.warning_message("AnnAGNPS_SIM_Ephemeral_Gully_Erosion output not found. \nGully column in OUTPUT OPTIONS DATA -SIM file must be set to T ")
                self.end_execution =True
                return
            csvreader = csv.reader(file)
            rows = []
            for row in csvreader:
                    rows.append(row)
            lista = []
            a = 0
            for i in rows:
                try:
                    if i[0]=="Day":
                        a = 1
                        lista.append(i)
                    elif a ==1:
                        lista.append(i[:-1])
                except:
                    continue
            erosion = [float(lista[x][27]) for x in range(1,len(lista)) if len(lista[x])==30]
            data_to_save["Ephemeral Gully erosion (Mg)"] = sum(erosion)'''
        
        #Pond erosion
        if self.sensitivity_dialog.pond.isChecked():
            df = self.import_df("Pond",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Sediment_yield_(mass) output not found. \nEV_Sed_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
            data_to_save["Pond erosion (Mg)"] = df_graph.sum() 
            
        #Sheet and rill erosion
        if self.sensitivity_dialog.sheet.isChecked():
            df = self.import_df("Sheet & Rill",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Sediment_yield_(mass) output not found. \nEV_Sed_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
            
            data_to_save["Sheet and rill erosion (Mg)"] = df_graph.sum() 
            
        #Nitrogen
        if self.sensitivity_dialog.nitrogen.isChecked():
            df = self.import_df("Nitrogen",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Nitrogen_yield_(mass) output not found. \nEV_N_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
            
            data_to_save["Nitrogen (kg)"] = df_graph.sum()
            
        #Organic carbon
        if self.sensitivity_dialog.organic.isChecked():
            df = self.import_df("Carbon",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Organic_Carbon_yield_(mass) output not found. \nEV_OC_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
            
            data_to_save["Organic Carbon (kg)"] = df_graph.sum()
            
        #Phosphorus
        if self.sensitivity_dialog.phosphorus.isChecked():
            df = self.import_df("Phosphorus",core,sensitivity=True)
            try:
                df_graph = df.groupby(df.index).sum(numeric_only=True)
            except:
                self.warning_message("AnnAGNPS_EV_Phosphorus_yield_(mass) output not found. \nEV_P_Yld_Mass column in OUTPUT OPTIONS DATA -EV file must be set to T ")
                self.end_execution =True
                return
            data_to_save["Phosphorus (kg)"] = df_graph.sum() 
        
        
        return data_to_save
    
    def create_df_sensitivity(self,results):
        """Method to create the dataframe of sensitivity after parallelization"""
        #First create dataframe
        df = pd.DataFrame(results)
        #Put in the same order as the input values
        new_df = pd.DataFrame(columns=list(df.columns))
        input_parameters = [x.replace("\n", " ") for x in self.dic_data.keys()]
        for i in self.param_values:
            df_concat = df.copy()
            for k in range(len(i)): 
                df_concat = df_concat[df_concat[input_parameters[k]]==i[k]]
            df_concat = df_concat.iloc[[0]]
            new_df = pd.concat([new_df,df_concat], ignore_index=True)
            
        return new_df
    
    
    def run_sensitivity_analysis_two(self):
        """Method to save the results of the sensitivity analysis and to calculate the sensitivity indexes"""
        #Organize the dataframe
        self.results_sensitivity = self.create_df_sensitivity(self.resultados)
        #Calculate sensitivity indexes
        path = self.direccion_sensitivity + "\\"+self.sensitivity_dialog.file_save.text()
        if self.sensitivity_dialog.sobol.isChecked():
            with open(path, 'w') as f:
                #Add first row
                f.write("Sobol sensitivity indexes (S1_S1 conf_ST_ST conf)" + '\n')
                #Add sensitivity indexes for each output
                for i in self.results_sensitivity.columns[len(self.dic_data):]:
                    f.write("----------------------------------------------------------------------" + '\n')
                    f.write(f"{i}" + '\n')
                    si = sobol.analyze(self.problem, np.array(self.results_sensitivity[i], dtype=float))
                    for input_parameter_k,input_parameter in enumerate(self.dic_data.keys()): 
                        input_parameter = input_parameter.replace('\n', ' ')
                        f.write(f"{input_parameter}:{si['S1'][input_parameter_k]}_{si['S1_conf'][input_parameter_k]}_{si['ST'][input_parameter_k]}_{si['ST_conf'][input_parameter_k]}" + '\n')
                f.write("----------------------------------------------------------------------" + '\n')
                
        elif self.sensitivity_dialog.morris.isChecked():
            with open(path, 'w') as f:
                #Add first row
                f.write("Morris sensitivity indexes (mu star_sigma_mu_mu star confidence)" + '\n')
                #Add sensitivity indexes for each output
                for i in self.results_sensitivity.columns[len(self.dic_data):]:
                    f.write("----------------------------------------------------------------------" + '\n')
                    f.write(f"{i}" + '\n')
                    si = analyze_morris(self.problem,np.array(self.param_values),np.array(self.results_sensitivity[i], dtype=float))
                    for input_parameter_k,input_parameter in enumerate(self.dic_data.keys()):    
                        input_parameter = input_parameter.replace('\n', ' ')
                        f.write(f"{input_parameter}:{si['mu_star'][input_parameter_k]}_{si['sigma'][input_parameter_k]}_{si['mu'][input_parameter_k]}_{si['mu_star_conf'][input_parameter_k]}" + '\n')
                f.write("----------------------------------------------------------------------" + '\n')
        
        #Append results
        self.results_sensitivity.to_csv(path, mode='a',index=False, float_format='%.10f')
        
        #Se cierra la barra de progreso
        self.progress_dialog.close()
        
        
        #Add csv result to the lineEdit and update graph
        if self.sensitivity_dialog.sobol.isChecked():
            self.dlg_results_sensitivity.radio_sobol.setChecked(True)
            self.dlg_results_sensitivity.csv_results_2.setText(path)
            self.update_sensitivity_graph_global()
        elif self.sensitivity_dialog.morris.isChecked():
            self.dlg_results_sensitivity.radio_morris.setChecked(True)
            self.dlg_results_sensitivity.csv_results_morris.setText(path)
            self.update_sensitivity_graph_global()
        
        #MENSAJE DE ÉXITO
        self.warning_message("Succes in the sensitiviy analysis ")
    
    
    def run_calibration_two(self):
        """Method to save the results of the calibration"""
        #Organize the dataframe
        self.results_calibration = pd.DataFrame(self.resultados)
        
        #Calculate sensitivity indexes
        path = self.direccion_sensitivity + "\\"+self.dlg_calibration.file_save.text()
        
        #Add best input combination and nash sutcliffe efficiency
        with open(path, 'w') as f:
            #Add first row
            f.write("Calibration results" + '\n')
            f.write("Optimized input values:" + '\n')
            for i in self.dic_data:
                f.write(f"{i}: "+str(self.best_result_calibration[1][i.replace('\n', ' ')]) + '\n')
            
            f.write(f"Nash-Sutcliffe efficiency: {self.best_result_calibration[1]['Nash_Sutcliffe']}" + '\n')
            f.write("Best combination results:\n")
        #Add best result
        self.best_result_calibration[0].to_csv(path, mode='a', index=False, float_format='%.10f')
        
        with open(path, 'a') as f:
            #Add first row
            f.write("Results of each iteration" + '\n')
            
        #Append results
        self.results_calibration.to_csv(path, mode='a', index=False, float_format='%.10f')
        
        #Se cierra la barra de progreso
        self.progress_dialog.close()
        
        #MENSAJE DE ÉXITO
        self.warning_message("Succes in the calibration")
    
    
    def calibration_bootstraping_show(self):
        """Method to make the bootstraping for the calibrated hydrograph and show dialog"""
        #Obtain data
        path = self.dlg_calibration_results.results.text()
        if os.path.exists(path) and os.path.isfile(path):    
            #First add the text
            with open(path, "r") as archivo:
                lineas = archivo.readlines()
            contenido = ""
            times = []
            observed = []
            simulated = []
            
            obtain_contenido = True
            
            for k,i in enumerate(lineas):
                if obtain_contenido:
                    contenido += i
                
                if "Nash-Sutcliffe efficiency" in i:
                    obtain_contenido = False
                    
                if i[:5]=="date,":
                    for m in range(k+1,len(lineas)):
                        if "Results of each iteration" in lineas[m]:
                            break
                        try:
                            times.append(pd.to_datetime(lineas[m].split(",")[0], errors='coerce'))
                        except:
                            times.append(0)
                        try:
                            observed.append(float(lineas[m].split(",")[1]))
                        except:
                            observed.append(0)
                        try:
                            simulated.append(float(lineas[m].split(",")[2]))
                        except:
                            simulated.append(0)
            
            
            #Obtain the expected length of block for the stationary bootsrapping according to Automatic Block-Length Selection for the Dependent Bootstrap (Dimitris N. Politis1 and Halbert White)
            def lambda_function(t):
                if abs(t)>=0 and abs(t)<=0.5:
                    return 1
                elif abs(t)>=0.5 and abs(t)<=1:
                    return 2*(1-abs(t))
                else:
                    0

            def r_function(k):
                n = len(observed)
                average = np.sum(observed)/len(observed)
                values = 0
                for i in range(n-abs(k)):
                    values += (observed[i]-average)/(observed[i+abs(k)]-average)
                return values/n


            def g_function(w):
                values = 0
                for i in range(-M,M):
                    values += lambda_function(i/M)*r_function(i)*math.cos(w*i)
                return values


            #Calculate G
            M = int(len(observed)/2)
            G = 0
            for i in range(-M,M):
                G += lambda_function(i/M)*abs(i)*r_function(i)

            #Calculate D
            integration_step = 0.1
            D = 4*(g_function(0)**2)
            values = 0
            w = -math.pi
            while w<math.pi:
                values += (1+math.cos(w))*(g_function(w)**2)*integration_step
                w += integration_step

            values = 2*values/math.pi
            D = D + values

            #Calculate optimal size of block
            b = (((2*(G**2))/D)**(1/3))*(len(observed)**(1/3))

            #Calculate probability for geometrical distribution after we calculated the expected length
            p = 1/b
            #if pequal or same as 1 then there is not distribution
            if p>=1: p = 0.9
            
            #Do the bootstrapping
            number_resamplings = 2000
            nash_list = []
            rmse_list = []
            for i in range(number_resamplings):
                observed_blocks = []
                simulated_blocks = []
                while len(observed_blocks)<len(observed):
                    index = np.random.randint(0, len(observed), dtype=int)
                    size = geom.rvs(p, size=1)[0]
                    if index+size>=len(observed):
                        block_observed = list(observed[index:])+list(observed[:(index+size)%len(observed)])
                        block_simulated = list(simulated[index:])+list(simulated[:(index+size)%len(simulated)])
                    else:
                        block_observed = list(observed[index:index+size])
                        block_simulated = list(simulated[index:index+size])
                        
                    observed_blocks += block_observed
                    simulated_blocks += block_simulated
                    
                observed_blocks = observed_blocks[:len(observed)]
                simulated_blocks = simulated_blocks[:len(simulated)]
                
                #Obtain indicators values
                observed_sample = np.array(observed_blocks)
                simulated_sample = np.array(simulated_blocks)
                #Caclulate nash
                mean_observed = np.mean(observed_sample)
                numerator = np.sum((observed_sample - simulated_sample) ** 2)
                denominator = np.sum((observed_sample - mean_observed) ** 2)
                nse = 1 - (numerator / denominator)
                nash_list.append(nse)
                #Calculate RMSE
                rmse = np.sqrt(np.mean((observed_sample - simulated_sample) ** 2))
                rmse_list.append(rmse)
            
            
            #Create variable to be obtained in other method
            self.nashes_bootstraping= nash_list
            self.rmse_bootstraping = rmse_list
            
            #Update graph
            self.calibration_bootstraping_update()
            
            #Show dialog
            self.dlg_fiteval_calibration.show()
            self.dlg_fiteval_calibration.raise_()

    
    def update_values_bootstrapping(self):
        """Method to update values in th evaluation of calibration"""
        try:
            dialog = self.dlg_fiteval_calibration

                
            #Obtain values
            values = [x for x in self.nashes_bootstraping if not np.isnan(x)]
            values_rmse = [x for x in self.rmse_bootstraping if not np.isnan(x)]

            
            #Put p value
            p_value = sum(1 for nash in values if nash < float(dialog.nash.text())) / len(values)
            dialog.p_value.setText(f"p-value: {str(round(p_value,2))}")
            #Put confidence interval for nash
            median = str(round(stats.scoreatpercentile(values,50),2))
            percentile_25 = str(round(stats.scoreatpercentile(values,2.5),2))
            percentile_975 = str(round(stats.scoreatpercentile(values,97.5),2))
            
            dialog.label_3.setText(f"NSE [95%CI]: {median}[{percentile_25} - {percentile_975}]")

            #Same for RMSE
            median = f"{stats.scoreatpercentile(values_rmse,50):.2e}"
            percentile_25 = f"{stats.scoreatpercentile(values_rmse,2.5):.2e}"
            percentile_975 = f"{stats.scoreatpercentile(values_rmse,97.5):.2e}"
            
            dialog.label_7.setText(f"RMSE [95%CI]: {median}[{percentile_25} - {percentile_975}]")
            
            
        except:
            pass
    
    def calibration_bootstraping_update(self):
        """Method to update graph of bootstraping fo hydrograph"""
        #Update values in lineEdits
        self.update_values_bootstrapping()
        
        #Add the graph
        canvas = "canvas_calibration_bootstrap"
        dialog = self.dlg_fiteval_calibration

            
        if not hasattr(self, canvas):
            #Create the canvas of the graph
            # Si no existe, crear el canvas y añadirlo al layout
            setattr(self,canvas,FigureCanvas(plt.Figure(figsize=(15, 6))))
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(dialog.frame)
            dialog.frame.setLayout(layout)
            #Add canvas to layout
            layout.addWidget(getattr(self,canvas))
        
        #Add graph
        getattr(self,canvas).figure.clear()
        ax1 = getattr(self,canvas).figure.subplots()

        # Histograma
        finite_nse = [nse for nse in self.nashes_bootstraping if nse != -np.inf]
        inf_count = len([nse for nse in self.nashes_bootstraping if nse == -np.inf])
        
        counts, bins, patches = ax1.hist(
            finite_nse, bins=20, density=True, alpha=0.7, color="lightcoral", edgecolor="black", label="Histogram"
        )

        # Función acumulada
        nashes = np.sort([x for x in self.nashes_bootstraping if not np.isnan(x)])
        
        cumulative = [np.searchsorted(nashes, b, side='right') / len(nashes) for b in bins]
        ax2 = ax1.twinx()
        ax2.plot(bins, cumulative, color="teal", lw=2, label="Cumulative")
        
        
        if inf_count>0:
            ax2.set_title(f"-Inf cases: {inf_count}")
        
        #Vertical line
        try:
            ax1.axvline(x=float(dialog.nash.text()), color='red', linestyle='--', linewidth=1.5)
            ax2.hlines(y=float(dialog.p_value.text().split(":")[-1]), xmin=float(dialog.nash.text()), xmax=ax2.get_xlim()[1],transform=ax2.get_yaxis_transform(),color='red', linestyle='--', linewidth=1.5)
        except:
            pass

        # Etiquetas de los ejes
        ax1.set_xlabel("Nash–Sutcliffe Efficiency")
        ax1.set_ylabel("Density")
        ax2.set_ylabel("Cumulative Probability")


        # Personalización de los grids
        ax1.grid(visible=True, linestyle="--", linewidth=0.6, alpha=0.5)
        ax2.grid(visible=False)

        # Leyendas
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        legend = ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")
        
        #Change background color
        getattr(self,canvas).figure.set_facecolor('#f0f0f0')
        ax1.set_facecolor('#f0f0f0')
        # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
        getattr(self,canvas).figure.subplots_adjust(left=0.2, bottom=0.2,right = 0.8)
        #Draw canvas
        getattr(self,canvas).draw()
        
        #Save figure
        self.dlg_fiteval_calibration.print_graph.clicked.connect(lambda _, b= [self.dlg_fiteval_calibration,getattr(self,canvas)]:self.figure_settings(b))
       
    def declare_rasters_sensitivity_analysis(self,information):
        """Method to declare the values of the rasters in sensitivity analysis"""
        #Function to transform from the path where the file is saved to the new path where sensitivity analysis is going to be performed
        def change_direction(name):
            try:
                ruta = str(project_df[project_df.iloc[:,0]==name].iloc[0,1])
                if ruta == "nan":
                    return "nan"
                ruta_nueva = Path(ruta).parts[-2:]
                resultado = str(Path(*ruta_nueva))
                return self.dlg.project.text()+"\\"+selected_project +f"\\{information}\\Core_1" +"\\"+resultado
            except:
                return "nan"
        
        
        
        #Obtain CSV
        if information =="Sensitivity_analysis":
            selected_project = self.sensitivity_dialog.project_sensitivity.currentText()
        elif information == "Calibration":
            selected_project = self.dlg_calibration.project_calibration.currentText()
        csv_file = self.carpeta_guardar_proyectos +"\\"+selected_project+"\\"+selected_project+".csv"
        project_df = pd.read_csv(csv_file,encoding = "ISO-8859-1",delimiter=",")
        self.project_df = project_df
        
        #Obtain the direction of sensitivity analysis
        #no hay que usar el self direccion porque se puede dar el caso en el que el se hace un analisis de sensibilidad sin haber escogido el nombre del proyecto en el dialogo base, es por eso que hay que crear otra variable que sea igual a working directory mas el nombre que se ha escogido en sensitivity
        self.direccion_sensitivity = self.dlg.project.text()+"\\"+selected_project +f"\\{information}"
        
        #DEM
        self.fichero_mdt_sensitivity =  change_direction("dem")
        _,self.name_mdt_sensitivity = os.path.split(self.fichero_mdt_sensitivity)
        
        #Buffer
        self.fichero_buf_sensitivity =  change_direction("buffer_layer")
        _,self.name_buffer_sensitivity= os.path.split(self.fichero_buf_sensitivity)
        
        #Vegetation
        self.fichero_veg_sensitivity =  change_direction("vegetation_layer")
        _,self.name_vegetation_sensitivity= os.path.split(self.fichero_veg_sensitivity)
        
        #Soil
        self.fichero_soil_sensitivity=  change_direction("soil_layer")
        _,self.name_soil_sensitivity = os.path.split(self.fichero_soil_sensitivity)
        self.unique_soil_sensitivity = project_df[project_df.iloc[:,0]=="unique_soil"].iloc[0,1]
        self.column_soil_sensitivity = project_df[project_df.iloc[:,0]=="soil_column"].iloc[0,1]
        
        #Management
        self.fichero_manag_sensitivity =  change_direction("use_layer")
        _,self.name_soil_sensitivity = os.path.split(self.fichero_manag_sensitivity)
        self.unique_use_sensitivity = project_df[project_df.iloc[:,0]=="unique_landuse"].iloc[0,1] 
        self.column_use_sensitivity = project_df[project_df.iloc[:,0]=="use_column"].iloc[0,1]
        
        #Epsg
        self.epsg_sensitivity = project_df[project_df.iloc[:,0]=="epsg"].iloc[0,1]
    
    
        
    
    def file_input(self,lineEdit):
        #Metod to go from line edit to the final direction
        #If input is topagnps provided then return correct path
        if lineEdit == self.inputs.l_3 and lineEdit.text()=="-- Provided by TopAGNPS --": #cell data
            return self.direccion+"\\INPUTS\\watershed\\"+"AnnAGNPS_Cell_Data_Section.csv"
        elif lineEdit == self.inputs.l_5 and lineEdit.text()=="-- Provided by TopAGNPS --": #ephemeral gully
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\"+"AGWET.csv"):
                return self.direccion+"\\INPUTS\\watershed\\"+"AnnAGNPS_Ephemeral_Gully_Data_Section_Revised_by_AgWet.csv"
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\"+"Agbuf.csv"):
                return self.direccion+"\\INPUTS\\watershed\\"+"AnnAGNPS_Ephemeral_Gully_Data_Section_Revised_by_AgBuf.csv"
            if os.path.exists(self.direccion+"\\Preprocessing_inputs"+"\\"+"PEG.csv"):
                return self.direccion+"\\INPUTS\\watershed\\"+"AnnAGNPS_Ephemeral_Gully_Data_Section.csv" 
        elif lineEdit == self.inputs.l_10 and lineEdit.text()=="-- Provided by TopAGNPS --": #reach
            return self.direccion+"\\INPUTS\\watershed\\"+"AnnAGNPS_Reach_Data_Section.csv"
        elif lineEdit == self.inputs.l_13 and lineEdit.text()=="-- Provided by TopAGNPS --": #wetland
            return self.direccion+"\\INPUTS\\watershed\\"+"AnnAGNPS_Wetland_Data_Section.csv"
        elif lineEdit == self.inputs.l_41 and lineEdit.text()=="-- Provided by TopAGNPS --": #buffer
            return self.direccion+"\\INPUTS\\general\\"+"AnnAGNPS_Riparian_Buffer_Data_Section_AgBuf.csv"
   
        #Else
        if os.path.isabs(lineEdit.text()):
            return lineEdit.text()
        else:
            return self.dic_folder[lineEdit].text()+"/"+lineEdit.text()
        
    
    def progress_metod(self,type_analysis,start=False,values=None,execution=None,close = False):
        #Metod to add and update de progress bar
        if start == True:
            #Start of the progress bar
            self.progress_dialog = QProgressDialog(f"Starting {type_analysis} analysis...", "Cancelar", 0, 101)
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setWindowTitle("Progress")
            self.progress_dialog.show()
            QCoreApplication.processEvents()# Permitir que la interfaz gráfica responda
        elif not close:
            #Updates of progress bar
            #Creation of text
            text = f"Execution {execution}/{len(self.param_values)}\n"
            for key in range(len(self.dic_data)):
                text+= str([x.replace('\n','') for x in self.dic_data.keys()][key])+":"+str(round(values[key],2))+"\n"
            #Add updates
            self.progress_dialog.setLabelText(text)
            self.progress_dialog.setValue(int(100*(execution/len(self.param_values))))
            QCoreApplication.processEvents()# Permitir que la interfaz gráfica responda
        #Close progress bar
        if close:
            self.progress_dialog.close()
    
    def search_sensitiviy_input(self):
        #Metod to search a sensitiviy input in the dialog writing
        texto = str(self.sensitivity_dialog.search.text())
        #If text == "" then delete every button
        if texto =="":
            while self.sensitivity_dialog.verticalLayout_3.count():
                child = self.sensitivity_dialog.verticalLayout_3.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            elementos = []
            for i in self.dic_name_column.keys():
                if texto.lower() in i.lower():
                    elementos.append(i)
            try: #if it doesnt find a name
                #Delete all elements of vertical layout of scroll area
                while self.sensitivity_dialog.verticalLayout_3.count():
                    child = self.sensitivity_dialog.verticalLayout_3.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                #Add new button to the scroll area
                for nombre in elementos:
                    boton = QtWidgets.QPushButton(nombre, self.sensitivity_dialog.scrollAreaWidgetContents_3)
                    boton.setObjectName(nombre)
                    self.sensitivity_dialog.verticalLayout_3.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = nombre: self.add_parameter_label(b))
            except:
                pass
    
    def search_calibration_input(self):
        #Metod to search a sensitiviy input in the dialog writing
        texto = str(self.dlg_calibration.search.text())
        #If text == "" then delete every button
        if texto =="":
            while self.dlg_calibration.verticalLayout_3.count():
                child = self.dlg_calibration.verticalLayout_3.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        else:
            elementos = []
            for i in self.dic_name_column.keys():
                if texto.lower() in i.lower():
                    elementos.append(i)
            try: #if it doesnt find a name
                #Delete all elements of vertical layout of scroll area
                while self.dlg_calibration.verticalLayout_3.count():
                    child = self.dlg_calibration.verticalLayout_3.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                #Add new button to the scroll area
                for nombre in elementos:
                    boton = QtWidgets.QPushButton(nombre, self.dlg_calibration.scrollAreaWidgetContents_3)
                    boton.setObjectName(nombre)
                    self.dlg_calibration.verticalLayout_3.addWidget(boton)
                    política_tamaño = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                    boton.setSizePolicy(política_tamaño)
                    boton.clicked.connect(lambda _, b = nombre: self.add_parameter_label_calibration(b))
            except:
                pass
    
    def change_bounds(self):
        #Metod to change bounds names if distribution changed
        def change_lines(bound1,bound2,bound3=None,bound4=None):
            self.sensitivity_dialog.label_3.setText(bound1)
            self.sensitivity_dialog.label_4.setText(bound2)
        distribution = [self.sensitivity_dialog.distributions.itemText(i) for i in range(self.sensitivity_dialog.distributions.count())][self.sensitivity_dialog.distributions.currentIndex()]
        
        if distribution=="Uniform":
            change_lines("Minimum","Maximum")
        if distribution=="Logaritmic uniform":
            change_lines("Minimum","Maximum")
        if distribution=="Triangular":
            change_lines("Minimum","Maximum","Peak")
        if distribution=="Normal":
            change_lines("Mean","Standard deviation")
        if distribution=="Lognormal":
            change_lines("Mean","Standard deviation")
        if distribution=="Normal truncated":
            change_lines("Minimum","Maximum","Mean","Standard deviation")
    
    def distribution_parameters(self):
        #Add/delete new labels depending on choosed distribution
        distribution = [self.sensitivity_dialog.distributions.itemText(i) for i in range(self.sensitivity_dialog.distributions.count())][self.sensitivity_dialog.distributions.currentIndex()]
        
        # Obtén el número de filas actual en el GridLayout
        numRows = self.sensitivity_dialog.gridLayout_3.rowCount()
        
        def delete_elements(row,column):
            widget = self.sensitivity_dialog.gridLayout_3.itemAtPosition(row, column).widget()
            self.sensitivity_dialog.gridLayout_3.removeWidget(widget)
            widget.deleteLater()
        
        if distribution=="Uniform":
            #Primero se borra
            try:
                delete_elements(4,0)
                delete_elements(4,1)
                delete_elements(5,0)
                delete_elements(5,1)
            except:
                pass
        
        elif distribution=="Logaritmic uniform":
            #Primero se borra
            try:
                delete_elements(4,0)
                delete_elements(4,1)
                delete_elements(5,0)
                delete_elements(5,1)
            except:
                pass
            
 
        elif distribution=="Triangular":
            #Primero se borra
            try:
                delete_elements(4,0)
                delete_elements(4,1)
                delete_elements(5,0)
                delete_elements(5,1)
            except:
                pass
            #Luego se añade
            # Crea un nuevo QLabel y QLineEdit
            newLabel = QLabel("Peak")
            self.sensitivity_dialog.third = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.sensitivity_dialog.gridLayout_3.addWidget(newLabel, 4, 0)
            self.sensitivity_dialog.gridLayout_3.addWidget(self.sensitivity_dialog.third, 4, 1)

        elif distribution=="Normal":
            #Primero se borra
            try:
                delete_elements(4,0)
                delete_elements(4,1)
                delete_elements(5,0)
                delete_elements(5,1)
            except:
                pass
        
        if distribution=="Lognormal":
            #Primero se borra
            try:
                delete_elements(4,0)
                delete_elements(4,1)
                delete_elements(5,0)
                delete_elements(5,1)
            except:
                pass

        
        if distribution=="Normal truncated":
            #Primero se borra
            try:
                delete_elements(4,0)
                delete_elements(4,1)
                delete_elements(5,0)
                delete_elements(5,1)
            except:
                pass
            #Luego se añade
            # Crea un nuevo QLabel y QLineEdit
            newLabel = QLabel("Mean")
            self.sensitivity_dialog.third = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.sensitivity_dialog.gridLayout_3.addWidget(newLabel, 4, 0)
            self.sensitivity_dialog.gridLayout_3.addWidget(self.sensitivity_dialog.third, 4, 1)
            
            # Crea un nuevo QLabel y QLineEdit
            newLabel = QLabel("Standard deviation")
            self.sensitivity_dialog.fourth = QLineEdit()
            # Agrega el nuevo QLabel y QLineEdit a la siguiente fila
            self.sensitivity_dialog.gridLayout_3.addWidget(newLabel, 5, 0)
            self.sensitivity_dialog.gridLayout_3.addWidget(self.sensitivity_dialog.fourth, 5, 1)
    
    def change_sensitivity_metod(self):
        #Metod to change sensitivity inputs depending on selected senstitivity metod
        if self.sensitivity_dialog.sobol.isChecked():
            self.sensitivity_dialog.label_5.setText("M")
            try:
                if self.sensitivity_dialog.trajectories.text()=="" or self.sensitivity_dialog.table.rowCount()==0:
                    self.sensitivity_dialog.lineEdit_6.setText("")
                else:
                    self.sensitivity_dialog.lineEdit_6.setText(str(int(self.sensitivity_dialog.trajectories.text())*(2*self.sensitivity_dialog.table.rowCount()+2)))
                #Change the file output
                self.sensitivity_dialog.file_save.setText("sensitivity_sobol.csv")
            except:
                pass
        elif self.sensitivity_dialog.morris.isChecked():
            self.sensitivity_dialog.label_5.setText("Trajectories")
            try:
                if self.sensitivity_dialog.trajectories.text()=="" or self.sensitivity_dialog.table.rowCount()==0:
                    self.sensitivity_dialog.lineEdit_6.setText("")
                else:
                    self.sensitivity_dialog.lineEdit_6.setText(str(int(self.sensitivity_dialog.trajectories.text())*(self.sensitivity_dialog.table.rowCount()+1)))
                #Change the file output
                self.sensitivity_dialog.file_save.setText("sensitivity_morris.csv")
            except:
                pass
    
    def update_sensitivity_graph_global(self):
        """Method to update the graph of the sensitivity for Sobol"""
        #Create and clear axis before drawing
        if not hasattr(self, 'canvas_sensitivity_graph'):
            # Si no existe, crear el canvas y añadirlo al layout
            self.canvas_sensitivity_graph = FigureCanvas(plt.Figure(figsize=(15, 6)))
            
            # Asignar un layout al QFrame si no tiene uno
            layout = QVBoxLayout(self.dlg_results_sensitivity.frame_64)
            self.dlg_results_sensitivity.frame_64.setLayout(layout)
            
            # Añadir el canvas al layout
            layout.addWidget(self.canvas_sensitivity_graph)
        else:
            # Si ya existe, simplemente limpiar el canvas
            self.canvas_sensitivity_graph.figure.clear()
        
        #Function to convert nans to 0
        def nan_function(value):    
            if value.replace("\n","") == "nan":
                return 0
            try:
                return float(value)
            except:
                return 0
        
        #Sensitivity graphs
        if self.dlg_results_sensitivity.radio_sensitivity.isChecked():
            #MORRIS
            if self.dlg_results_sensitivity.radio_morris.isChecked():
                ruta = self.dlg_results_sensitivity.csv_results_morris.text()
                if os.path.exists(ruta) and os.path.isfile(ruta):
                    with open(ruta, "r") as archivo:
                        lineas = archivo.readlines()
                    #If the csv is not of a Morris sensitivity analysis then give error
                    if lineas[0]!="Morris sensitivity indexes (mu star_sigma_mu_mu star confidence)" + '\n':
                        self.warning_message("Please select a csv file that contains Morris sensitivity analysis results")
                        return
                    
                    #Obtain output
                    for i in range(self.dlg_results_sensitivity.frame_18.layout().count()):
                        item = self.dlg_results_sensitivity.frame_18.layout().itemAt(i)
                        widget = item.widget()
                        
                        #Checks if the widget is a QCheckBox and if it is selected.
                        if isinstance(widget, QRadioButton) and widget.isChecked():
                            output_column = widget.text()
                    
                    names_inputs = []
                    mu_star = []
                    sigma = []
                    mu = []
                    mu_star_conf = []
                    for i in range(len(lineas)):
                        if lineas[i] == output_column+ '\n':
                            for k in lineas[i+1:]:
                                if k == "----------------------------------------------------------------------" + '\n':
                                        break
                                names_inputs.append(k.split(":")[0])
                                mu_star.append(nan_function(k.split(":")[1].split("_")[0]))
                                sigma.append(nan_function(k.split(":")[1].split("_")[1]))
                                mu.append(nan_function(k.split(":")[1].split("_")[2]))
                                mu_star_conf.append(nan_function(k.split(":")[1].split("_")[3]))
                    
                    #If output doesnt exist, then stop with the code
                    if len(mu_star) == 0:
                        self.canvas_sensitivity_graph.figure.clear()
                        #If I clear but not .draw() then is changed but only when dialog is maximized or minimized
                        self.canvas_sensitivity_graph.draw()
                        return
                        
                    self.ax = self.canvas_sensitivity_graph.figure.subplots()
                    # Graficar los puntos con color granate y agregar etiquetas
                    add_label_monotonic = True # add label only once
                    add_label_non_monotonic = True # add label only once
                    for i, (x, y,conf) in enumerate(zip(mu_star, sigma,mu_star_conf)):
                        if np.isnan(x):x = 0
                        if np.isnan(y):y = 0
                        #If the difference between mu and mu star is higher than 5%, then is non-monotonic
                        if abs(mu_star[i]) == 0 and abs(mu_star[i]) == 0:
                            difference = 0
                        elif abs(mu_star[i]) != 0 and abs(mu_star[i]) == 0:
                            difference = 1
                        else:
                            difference = (abs(mu_star[i])-abs(mu[i]))/abs(mu_star[i])
                        if difference>0.05:
                            if add_label_non_monotonic: # add label only once
                                self.ax.errorbar(x, y, xerr = conf,color="blue",ecolor='black', marker="*", label="Non-Monotonic", capsize=5)
                                add_label_non_monotonic = False
                            else:
                                self.ax.errorbar(x, y, xerr = conf, color="blue",ecolor='black', marker="*", capsize=5)
                            self.ax.annotate("\n".join(textwrap.wrap(names_inputs[i], width=20, break_long_words=False)), (x, y), textcoords="offset points", xytext=(10,10), ha='center', 
                                fontweight='bold',fontsize = 10)
                        else:
                            if add_label_monotonic: # add label only once
                                self.ax.errorbar(x, y,xerr = conf, marker="o", color="maroon",ecolor='black',label="Monotonic", capsize=5)
                                add_label_monotonic = False
                            else:
                                self.ax.errorbar(x, y, xerr = conf,marker="o", color="maroon",ecolor='black', capsize=5)
                                
                            self.ax.annotate("\n".join(textwrap.wrap(names_inputs[i], width=20, break_long_words=False)), (x, y), textcoords="offset points", xytext=(10,10), ha='center', 
                                fontweight='bold',fontsize = 10)
                            
                    #Linea 1:1
                    line_plot = list(range(-1,int(max([mu_star[x]+mu_star_conf[x] for x in range(len(mu_star))]+list(sigma))*1.1)+2))
                    self.ax.plot(line_plot, line_plot, color="red",linestyle="--")
                    
                    if max(list(mu_star)+list(sigma))>0:
                        self.ax.set_xlim(0,max([mu_star[x]+mu_star_conf[x] for x in range(len(mu_star))]+list(sigma))*1.1)
                        self.ax.set_ylim(0,max([mu_star[x]+mu_star_conf[x] for x in range(len(mu_star))]+list(sigma))*1.1)
                    else:
                        self.ax.set_xlim(0,1)
                        self.ax.set_ylim(0,1)
                    
                    #Add legend
                    legend = self.ax.legend(
                        loc="lower center",  # Centrar horizontalmente
                        bbox_to_anchor=(0.9, 1.01),  # Posición justo arriba del gráfico
                        ncol=1,  # Número de columnas en la leyenda
                        frameon=False
                    )
                    legend.get_frame().set_alpha(0)
            
                    #Labels
                    self.ax.set_xlabel(r"Mean of Elementary Effects ($\mu_{i}^{*}$)")
                    self.ax.set_ylabel("Standard Deviation of Elementary Effects ($\sigma_{i}$)")
                    self.ax.set_title("Morris sensitivity analysis indexes")
                    #Change background color
                    self.canvas_sensitivity_graph.figure.set_facecolor('#f0f0f0')
                    self.ax.set_facecolor('#f0f0f0')
                    # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                    self.canvas_sensitivity_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
                    #Draw canvas
                    self.canvas_sensitivity_graph.draw()
                
                else: #if path doesnt exist then clear figure
                    self.canvas_sensitivity_graph.figure.clear()
                    #If I clear but not .draw() then is changed but only when dialog is maximized or minimized
                    self.canvas_sensitivity_graph.draw()
                    
            
            
            #Sobol
            elif self.dlg_results_sensitivity.radio_sobol.isChecked():
                ruta = self.dlg_results_sensitivity.csv_results_2.text()
                if os.path.exists(ruta) and os.path.isfile(ruta):
                    with open(ruta, "r") as archivo:
                        lineas = archivo.readlines()
                    #If the csv is not of a Sobol sensitivity analysis then give error
                    if lineas[0]!="Sobol sensitivity indexes (S1_S1 conf_ST_ST conf)" + '\n':
                        self.warning_message("Please select a csv file that contains Sobol sensitivity analysis results")
                        return
                    
                    #Create and clear axis before drawing
                    self.canvas_sensitivity_graph.figure.clear()
                    self.ax_sobol = self.canvas_sensitivity_graph.figure.subplots(1, 2)
                    
                    #Obtain output
                    for i in range(self.dlg_results_sensitivity.frame_18.layout().count()):
                        item = self.dlg_results_sensitivity.frame_18.layout().itemAt(i)
                        widget = item.widget()
                        
                        #Checks if the widget is a QCheckBox and if it is selected.
                        if isinstance(widget, QRadioButton) and widget.isChecked():
                            output_column = widget.text()
                    
                    names_inputs = []
                    s1 = []
                    s1_conf = []
                    st = []
                    st_conf = []
                    for i in range(len(lineas)):
                        if lineas[i] == output_column+ '\n':
                            for k in lineas[i+1:]:
                                if k == "----------------------------------------------------------------------" + '\n':
                                        break
                                names_inputs.append(k.split(":")[0]) 
                                s1.append(nan_function(k.split(":")[1].split("_")[0]))
                                s1_conf.append(nan_function(k.split(":")[1].split("_")[1]))
                                st.append(nan_function(k.split(":")[1].split("_")[2]))
                                st_conf.append(nan_function(k.split(":")[1].split("_")[3]))
                    
                    #If output doesnt exist, then stop with the code
                    if len(s1) == 0:
                        self.canvas_sensitivity_graph.figure.clear()
                        #If I clear but not .draw() then is changed but only when dialog is maximized or minimized
                        self.canvas_sensitivity_graph.draw()
                        return
                    
                    #Total order 
                    self.ax_sobol[0].bar(names_inputs, st, yerr=st_conf, capsize=5, color='b')
                    self.ax_sobol[0].set_title('Sobol Total order index (ST)', fontsize=10)
                    self.ax_sobol[0].set_ylabel('Sobol index')
                    self.ax_sobol[0].tick_params(axis='x', rotation=90,labelsize = 10)
                    for label in self.ax_sobol[0].get_xticklabels():
                        label.set_ha('right')
                    
                    #First order 
                    self.ax_sobol[1].bar(names_inputs, s1, yerr=s1_conf, capsize=5, color='b')
                    self.ax_sobol[1].set_title('Sobol First order index (S1)', fontsize=10)
                    self.ax_sobol[1].tick_params(axis='x', rotation=90,labelsize = 10)
                    for label in self.ax_sobol[1].get_xticklabels():
                        label.set_ha('right')
                    
                    #Change background color
                    self.canvas_sensitivity_graph.figure.set_facecolor('#f0f0f0')
                    self.ax_sobol[0].set_facecolor('#f0f0f0')
                    self.ax_sobol[1].set_facecolor('#f0f0f0')
                    
                    # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                    self.canvas_sensitivity_graph.figure.subplots_adjust(wspace=0.4) #spacing beteween two graphs
                    self.canvas_sensitivity_graph.figure.subplots_adjust(left=0.2, bottom=0.2)
                    #Draw canvas
                    self.canvas_sensitivity_graph.draw()
                
                else: #if path doesnt exist then clear figure
                    self.canvas_sensitivity_graph.figure.clear()
                    #If I clear but not .draw() then is changed but only when dialog is maximized or minimized
                    self.canvas_sensitivity_graph.draw()
            
                
        #Uncertainity graphs
        elif self.dlg_results_sensitivity.radio_uncertainty.isChecked():
            try:
                #Warning messages
                if self.dlg_results_sensitivity.radio_morris.isChecked():
                    ruta = self.dlg_results_sensitivity.csv_results_morris.text()
                elif self.dlg_results_sensitivity.radio_sobol.isChecked():
                    ruta = self.dlg_results_sensitivity.csv_results_2.text()
                if os.path.exists(ruta):
                    with open(ruta, "r") as archivo:
                        lineas = archivo.readlines()
                    #If the csv is not of a Uncertainity sensitivity analysis then give error
                    if lineas[0]!="Uncertainty analysis results" + '\n' and lineas[0]!="Morris sensitivity indexes (mu star_sigma_mu_mu star confidence)" + '\n' and lineas[0]!="FAST sensitivity indexes S1_S1 conf_ST_ST conf" + '\n' and lineas[0]!="Sobol sensitivity indexes (S1_S1 conf_ST_ST conf)" + '\n':
                        self.warning_message("Please select a csv file that contains Uncertainity analysis results")
                        return
                        
                    self.ax_uncertainity = self.canvas_sensitivity_graph.figure.subplots(1,2)
                    
                    #Obtain data 
                    with open(ruta, "r") as archivo:
                         lines = archivo.readlines()
                    #Function to give nan if the value is not a number
                    def nan_function(value):    
                        if value.replace("\n","") == "nan":
                            return np.nan
                        try:
                            return float(value)
                        except:
                            return np.nan
                    
                    #When we see column error then we have the data
                    for index in range(len(lines)):
                        if len(lines[index].split(","))>2:
                            columns = [x.replace('\n', '') for x in lines[index].split(",")]
                            rows = []
                            for i in range(index+1,len(lines)):
                                rows.append([nan_function(x) for x in lines[i].split(",")])
                            break


                    df = pd.DataFrame(rows, columns=columns)
                    
                    #Get output
                    for i in range(self.dlg_results_sensitivity.frame_18.layout().count()):
                        item = self.dlg_results_sensitivity.frame_18.layout().itemAt(i)
                        widget = item.widget()
                        
                        #Checks if the widget is a QCheckBox and if it is selected.
                        if isinstance(widget, QRadioButton) and widget.isChecked():
                            output_column = widget.text()
                    
                    
                    y = [float(x) for x in df[output_column] if x!=np.nan]
                    
                    bins = 30
                    self.ax_uncertainity[0].hist(y, bins=bins, edgecolor='black')
                    #Labels
                    output_with_line_breaks = "\n".join(textwrap.wrap(output_column, width=37, break_long_words=False))
                    self.ax_uncertainity[0].set_xlabel(output_with_line_breaks)
                    self.ax_uncertainity[0].set_ylabel("Frequency")
                    
                    ax2 = self.ax_uncertainity[0].twinx()
                    x_sorted = np.sort(y)
                    # Calcular la frecuencia acumulativa
                    acum = np.arange(1, len(x_sorted) + 1) / len(x_sorted)
                    # Graficar la frecuencia acumulativa con líneas
                    ax2.plot(x_sorted, acum, linestyle='-', marker='',color = "black")
                    ax2.set_ylabel("Cumulative Frequency")
                    #Put ax2 in the front
                    self.ax_uncertainity[0].set_zorder(1)
                    ax2.set_zorder(2)
                    #Delete grid
                    ax2.grid(visible=False)
                    
                    #Box plot
                    self.ax_uncertainity[1].boxplot(y)
                    self.ax_uncertainity[1].set_xticks([])
                    # Añadir título y etiquetas
                    self.ax_uncertainity[1].set_ylabel(output_with_line_breaks)
                    #Title to graph
                    self.canvas_sensitivity_graph.figure.suptitle(f"Uncertainty of {output_column}", fontsize = 10)
                    
                    #Change background color
                    self.canvas_sensitivity_graph.figure.set_facecolor('#f0f0f0')
                    self.ax_uncertainity[0].set_facecolor('#f0f0f0')
                    self.ax_uncertainity[1].set_facecolor('#f0f0f0')
                    # Ajustar los márgenes para añadir más espacio por debajo y por la izquierda
                    self.canvas_sensitivity_graph.figure.subplots_adjust(wspace=0.7) #spacing beteween two graphs
                    self.canvas_sensitivity_graph.figure.subplots_adjust(left=0.1, bottom=0.2)
                    #Draw canvas
                    self.canvas_sensitivity_graph.draw()
                
            except:
                # Clear canvas
                self.canvas_sensitivity_graph.figure.clear()
                self.ax_uncertainity[0].clear()
                self.ax_uncertainity[1].clear()
                self.canvas_sensitivity_graph.draw()
        
        
        #Save figure
        self.dlg_results_sensitivity.print_graph_sensitivity.clicked.connect(lambda _, b= [self.dlg_results_sensitivity,self.canvas_sensitivity_graph]:self.figure_settings(b))
    
    
    def figure_settings(self, information):
        """Method to select the settings of the image that is going to be saved"""
        self.dlg_figure_settings.show()
        self.information_figure_save = information
        
        
    def resample_rasters(self):
        #Metod to resample rasters
        orden_pixel = list(self.dic_data.keys()).index("Pixel Size") #columna en la que están los valores de tamaño de pixel
        for pixel_size in np.unique(self.param_values[:,orden_pixel]):
            self.nombre_mdt = self.name_mdt.rsplit(".", 1)[0] #nombre del archivo sin extensión
            self.extension_mdt = self.name_mdt.split(".")[-1] #extensión del archivo
            processing.run("gdal:warpreproject", 
                {'INPUT':self.fichero_mdt,'SOURCE_CRS':QgsCoordinateReferenceSystem(self.epsg),'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':round(float(pixel_size),2),'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,
                'MULTITHREADING':False,'EXTRA':'','OUTPUT':self.direccion+"\\"+self.nombre_mdt+f"_{round(pixel_size,2)}"+"."+self.extension_mdt})
            
            #If buffer exists then resample
            if self.dlg.comboBox_2.currentIndex()>0:
                self.nombre_buffer = self.name_buffer.rsplit(".", 1)[0] #nombre del archivo sin extensión
                self.extension_buffer = self.name_buffer.split(".")[-1] #extensión del archivo
                processing.run("gdal:warpreproject", 
                    {'INPUT':self.fichero_buf,'SOURCE_CRS':QgsCoordinateReferenceSystem(self.epsg),'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':round(float(pixel_size),2),'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,
                    'MULTITHREADING':False,'EXTRA':'','OUTPUT':str(self.direccion+"\\"+self.nombre_buffer+f"_{round(pixel_size,2)}"+"."+self.extension_buffer)})
            #If vegetation exists then resample
            if self.dlg.comboBox_3.currentIndex()>0:
                self.nombre_vegetation = self.name_vegetation.rsplit(".", 1)[0] #nombre del archivo sin extensión
                self.extension_vegetation = self.name_vegetation.split(".")[-1] #extensión del archivo
                processing.run("gdal:warpreproject", 
                    {'INPUT':self.fichero_veg,'SOURCE_CRS':QgsCoordinateReferenceSystem(self.epsg),'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':round(float(pixel_size),2),'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,
                    'MULTITHREADING':False,'EXTRA':'','OUTPUT':self.direccion+"\\"+self.nombre_vegetation+f"_{round(pixel_size,2)}"+"."+self.extension_vegetation})
    
    
    
    def resample_rasters_sensitivity(self):
        #Metod to resample rasters
        #Make directory first if it doesn´t exist
        destino = Path(self.direccion_sensitivity+"\\Resampled_rasters")
        destino.mkdir(parents=True, exist_ok=True)
        
        #Resample rasters
        orden_pixel = list(self.dic_data.keys()).index("Pixel Size") #columna en la que están los valores de tamaño de pixel
        for pixel_size in np.unique(self.param_values[:,orden_pixel]):
            self.nombre_mdt_sensitivity = self.name_mdt_sensitivity.rsplit(".", 1)[0] #nombre del archivo sin extensión
            self.extension_mdt_sensitivity = self.name_mdt_sensitivity.split(".")[-1] #extensión del archivo
            processing.run("gdal:warpreproject", 
                {'INPUT':self.fichero_mdt_sensitivity,'SOURCE_CRS':QgsCoordinateReferenceSystem(self.epsg),'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':round(float(pixel_size),2),'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,
                'MULTITHREADING':False,'EXTRA':'','OUTPUT':str(destino)+"\\"+self.nombre_mdt_sensitivity+f"_{round(pixel_size,2)}"+"."+self.extension_mdt_sensitivity})
            
            #If buffer exists then resample
            if self.dlg.comboBox_2.currentIndex()>0:
                self.nombre_buffer_sensitivity = self.name_buffer_sensitivity.rsplit(".", 1)[0] #nombre del archivo sin extensión
                self.extension_buffer_sensitivity = self.name_buffer_sensitivity.split(".")[-1] #extensión del archivo
                processing.run("gdal:warpreproject", 
                    {'INPUT':self.fichero_buf_sensitivity,'SOURCE_CRS':QgsCoordinateReferenceSystem(self.epsg),'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':round(float(pixel_size),2),'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,
                    'MULTITHREADING':False,'EXTRA':'','OUTPUT':str(str(destino)+"\\"+self.nombre_buffer_sensitivity+f"_{round(pixel_size,2)}"+"."+self.extension_buffer_sensitivity)})
            #If vegetation exists then resample
            if self.dlg.comboBox_3.currentIndex()>0:
                self.nombre_vegetation_sensitivity = self.name_vegetation_sensitivity.rsplit(".", 1)[0] #nombre del archivo sin extensión
                self.extension_vegetation_sensitivity = self.name_vegetation_sensitivity.split(".")[-1] #extensión del archivo
                processing.run("gdal:warpreproject", 
                    {'INPUT':self.fichero_veg_sensitivity,'SOURCE_CRS':QgsCoordinateReferenceSystem(self.epsg),'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':round(float(pixel_size),2),'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,
                    'MULTITHREADING':False,'EXTRA':'','OUTPUT':str(destino)+"\\"+self.nombre_vegetation_sensitivity+f"_{round(pixel_size,2)}"+"."+self.extension_vegetation_sensitivity})
        
    
            



class Sensitivity_Parallelization(QgsTask):
    def __init__(self, n, core,execute_preprocessing_sensitivity,direccion_sensitivity,dic_data,param_values,executable_directory,plugin_dir,dic_name_column,nombre_mdt_sensitivity,extension_mdt_sensitivity,fichero_buf_sensitivity,nombre_buffer_sensitivity,extension_buffer_sensitivity,fichero_veg_sensitivity,nombre_vegetation_sensitivity,extension_vegetation_sensitivity,inputs, epsg_sensitivity,unique_soil_sensitivity,fichero_soil_sensitivity,column_soil_sensitivity,unique_use_sensitivity,fichero_manag_sensitivity,column_use_sensitivity,project_df):
        super().__init__(f"Tarea_{n}_Carpeta_{core}")
        self.n = n
        self.core = core
        self.execute_preprocessing_sensitivity = execute_preprocessing_sensitivity
        self.direccion_sensitivity = direccion_sensitivity
        self.dic_data = dic_data
        self.param_values = param_values
        self.executable_directory = executable_directory
        self.plugin_dir = plugin_dir
        self.dic_name_column = dic_name_column
        self.nombre_mdt_sensitivity =nombre_mdt_sensitivity
        self.extension_mdt_sensitivity=extension_mdt_sensitivity
        self.fichero_buf_sensitivity=fichero_buf_sensitivity
        self.nombre_buffer_sensitivity=nombre_buffer_sensitivity
        self.extension_buffer_sensitivity=extension_buffer_sensitivity
        self.fichero_veg_sensitivity=fichero_veg_sensitivity
        self.nombre_vegetation_sensitivity=nombre_vegetation_sensitivity
        self.extension_vegetation_sensitivity=extension_vegetation_sensitivity
        self.inputs = inputs
        self.epsg_sensitivity = epsg_sensitivity
        self.unique_soil_sensitivity = unique_soil_sensitivity
        self.fichero_soil_sensitivity = fichero_soil_sensitivity
        self.column_soil_sensitivity = column_soil_sensitivity
        self.unique_use_sensitivity = unique_use_sensitivity
        self.fichero_manag_sensitivity = fichero_manag_sensitivity
        self.column_use_sensitivity = column_use_sensitivity
        self.project_df = project_df
        
        
    def run(self):
        # Ajusta la ruta para que use la carpeta correspondiente al folder_id
        
        self.end_execution = 0
        try:
            self.ejecucion_completa_sensitivity()
        except Exception as e:
            self.error_msg = str(e)
            return False
        if self.end_execution ==1:
            return False
        
        return True
    
    
    def ejecucion_completa_sensitivity(self):
        #Esta función es en donde se ejecuta el modelo
        #EJECUCIÓN DE TOPAGNPS
        if self.execute_preprocessing_sensitivity:
            #Se crea la carpeta de Preprocessing_inputs si no estaba creada. Ahí se meten los inputs y se ejecuta TopAGNPS y luego los outputs se meten a Preprocessing_outputs
            
            #Función para que se le diga el nombre del archivo y te devuelva la dirección completa
            def fichero(nombre):
                return self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\"+nombre
            
            #Dar error si no existe el archivo TOPAGNPS.CSV
            if not os.path.exists(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV"):
                self.error_msg = "Error Input data\nControl file of TopAGNPS, TOPAGNPS.CSV, not found"
                self.end_execution = 1
                return
            #Si el formato de la columna FILENAME no es str entonces dar error
            topagnps_control_file = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV",encoding = "ISO-8859-1",delimiter=",")
            if type(topagnps_control_file["FILENAME"].iloc[0])!=str:
                self.error_msg ="Error Input data\nPlease select a correct FILENAME in TOPAGNPS.CSV" 
                self.end_execution = 1
                return
            #si se está haciendo un análisis de sensibilidad entonces se cambian los inputs.
            for j,k in enumerate(self.dic_data.keys()):
                self.change_inputs_sensitivity(self.param_values[self.n-1],j,k,spatial =True) #cambio de los inputs espaciales
            #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
            self.time_start_preprocessing = datetime.now()
            #EJECUCIÓN DE TOPAGNPS            
            def main():
                f = open(self.executable_directory+"\\"+f"EjecutarTopagnps_{self.core}.bat","w+")
                linea_uno = "CD /d {}".format(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs")
                linea_dos = r"CALL {}\TopAGNPS_v6.00.a.025_release_64-bit.exe".format(self.executable_directory)
                f.write("{} \n".format(linea_uno))
                f.write("{} \n".format(linea_dos))
                f.close()
            main()
            subprocess.call(self.executable_directory+"\\"+f"EjecutarTopagnps_{self.core}.bat")
            #proc = subprocess.Popen(self.executable_directory+"\\"+"EjecutarTopagnps.bat", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            #stdout, stderr = proc.communicate()
            #If error file of TopAGNPS is opened, then return a error message
            try:
                open(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.csv", "r+") 
            except PermissionError:
                self.error_msg ="Error TopAGNPS","Close TOPAGNPS_err.csv before the start of execution"
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder_sensitivity()
                self.end_execution = 1
                return
            except:
                pass
            #Cuando se eligen coordenadas automáticamente con el plugin primero se ejecuta Topagnps y da error (se ejecuta la primera para poner el reaches en QGIS) osea que no queremos que python salte si hay error en la primera ronda. Queremos que salte python cuando hay error y si se ha seleccionado que no se elige automaticamente. O sino cuando hay error y se ha elegido automáticamente pero la segunda ejecución de Topagnps da error. 
            if os.path.isfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.CSV") and os.path.getsize(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.CSV")>0:
                self.end_execution = 1
                error = pd.read_csv(fichero("TOPAGNPS_err.CSV"),encoding = "ISO-8859-1",delimiter=",")
                self.error_msg =f"Error TOPAGNPS\n{error.columns[3]}"
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder_sensitivity()
                #Se abre el archivo de errores
                try:
                    os.startfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs"+"\\TopAGNPS_err.csv")
                except:
                    pass
                #Este return es para parar el codigo
                return
            
            #VALORES DEL TAMAÑO DE PIXEL
            layer = QgsRasterLayer(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\"+topagnps_control_file["FILENAME"].iloc[0],"dednm")
            self.pixelSizeX = round(layer.rasterUnitsPerPixelX(),2)
            self.pixelSizeY = round(layer.rasterUnitsPerPixelY(),2)
            #ASIGNAR LOS VALORES DE SUELO Y MANEJO A AnnAGNPS_Cell_Data_Section.csv
            try:
                self.add_soil_and_management_cell_sensitivity()
            except Exception as e:
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder_sensitivity()
                self.error_msg =str(e)
                
                error_completo = traceback.format_exc()
                
                
                return
            #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
            self.save_files_preprocessing_in_folder_sensitivity()
            
            #Move the outputs of TopAGNPS to use as inputs of AnnAGNPS 
            self.create_folder_processing_and_move_files()
            
        #EJECUCIÓN DE ANNAGNPS

        #MOVER EL ANNAGNPS.FIL (CREO QUE ES EL CONTROL FILE DE ANNAGNPS) A LA CARPETA DE INPUTS de procesamiento
        shutil.copyfile(self.plugin_dir+"\\Executables"  + "\\" +"AnnAGNPS.fil" ,self.direccion_sensitivity +f"\\Core_{self.core}"+"\\Processing_inputs\\" +"AnnAGNPS.fil")
        #Se cambian los inputs
        for j,k in enumerate(self.dic_data.keys()):
            self.change_inputs_sensitivity(self.param_values[self.n-1],j,k,spatial =False) #cambio de los inptus no espaciales
        
        
        
        #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
        self.time_start_processing = datetime.now()
        
        #EJECUCIÓN DE ANNAGNPS
        #os.chdir(self.direccion+"\\"+directory)
        def execute_bat():
           def main():
               f = open(self.executable_directory+"\\"+f"EjecutarAnnAGNPS_{self.core}.bat","w+")
               linea_uno = "CD /d {}".format(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs")
               linea_dos = r"CALL {}\AnnAGNPS_v6.00.r.058_release_64-bit.exe".format(self.executable_directory)
               f.write("{} \n".format(linea_uno))
               f.write("{} \n".format(linea_dos))
               f.close()
           main()
        execute_bat()
        r'''env = os.environ.copy()
        env['PATH'] = f'{self.executable_directory};' + env['PATH']
        command = self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='latin-1', env=env)'''

        subprocess.call(self.executable_directory+"\\"+f"EjecutarAnnAGNPS_{self.core}.bat")

        
                  
        #PONER MENSAJE DE ERROR SI ANNAGNPS FUNCIONA MAL
        time.sleep(1)
        if path.exists(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv"):
            if os.stat(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv").st_size>0:
                self.end_execution =1
                try:
                    text = open(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv", "r")
                    text = ''.join([i for i in text]) 
                    text = text.replace("\"", "/") 
                    texto = text.splitlines()
                    txt = texto[2].split(",")[-1]
                    self.error_msg = f"Error AnnAGNPS\n{txt}"
                except:
                    pass
                
                self.end_execution = 1
                #Se abre el archivo de errores
                try:
                    os.startfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv")
                except:
                    pass
                #Este return es para parar el codigo
                return 
        
        #EJECUCIÓN DEL OUTPUT_TABLES
        time.sleep(1)
        shutil.copyfile(self.executable_directory + "\\" +"STEAD.fil" ,self.direccion_sensitivity+f"\\Core_{self.core}" + "\\Processing_inputs\\" +"STEAD.fil")
        os.chdir(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs")
        proc = subprocess.Popen(self.executable_directory + "\\" +"STEAD.exe", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        
        #Los outputs de AnnAGNPS se guardan en Processing_outputs
        self.save_files_processing_in_folder_sensitivity()
    
    
    def save_files_preprocessing_in_folder_sensitivity(self):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Preprocessing_outputs if it doesn´t exist
        carpeta = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        
        
        
        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs")
        carpeta_destino = Path(carpeta)

        for f in carpeta_origen.iterdir():
            try:
                if f.is_file():
                    t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                    if t > self.time_start_preprocessing:
                        shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass
    
    
    def save_files_processing_in_folder_sensitivity(self):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Processing_outputs if it doesn´t exist
        carpeta = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        

        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs")
        carpeta_destino = Path(carpeta)
        
        archivo_excluido = Path(self.direccion_sensitivity+f"\\Core_{self.core}") / "Processing_inputs" / "AnnAGNPS.fil"
        
        for f in carpeta_origen.iterdir():
            try:
                t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                if t > self.time_start_processing and f != archivo_excluido:
                    shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass
    
    
    def change_inputs_sensitivity(self,param_values,numero_parametro,nombre_parametro,spatial):
        #Metod to change the inputs of sensitivity analysis
        try: #este try es para cuando cuando de error si elige la misma columna pero distintas filas
            if self.dic_name_column[nombre_parametro][0]=="Spatial" and spatial:
                direccion = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs\\"+self.dic_name_column[nombre_parametro][1]
                columna = self.dic_name_column[nombre_parametro][2]
            elif self.dic_name_column[nombre_parametro][0]!="Spatial" and not spatial:
                direccion = self.file_input(self.dic_name_column[nombre_parametro][0])
                columna = self.dic_name_column[nombre_parametro][1]
                
        except KeyError: #misma columna, distintas filas
            if self.dic_name_column[nombre_parametro.split("__")[0]][0]=="Spatial" and spatial:
                direccion = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs\\"+self.dic_name_column[nombre_parametro.split("__")[0]][1]
                columna = self.dic_name_column[nombre_parametro.split("__")[0]][2]
            elif self.dic_name_column[nombre_parametro.split("__")[0]][0]!="Spatial" and not spatial:
                direccion = self.file_input(self.dic_name_column[nombre_parametro.split("__")[0]][0])
                columna = self.dic_name_column[nombre_parametro.split("__")[0]][1]
            
        #Si el input es tamaño de pixel entonces la variable será un texto que seleccione al DEM con el tamaño de pixel determinado
        if nombre_parametro =="Pixel Size" and spatial:
            self.change_control_files_pixel(param_values,numero_parametro)
        elif self.dic_name_column[nombre_parametro][1]=="AGFLOW.csv" and spatial:#in the case of agflow the input change is different
            #First we add the data of control files to the dialog. This is important because the rest of the values that are not changed need to be taken from the control file.
            self.asignar_valores_control_dialogo()
            #Then we change the inputs of agflow control file
            fichero = open(self.plugin_dir+r"\Documentos\agflow.inp","r+")
            texto = fichero.read()
            fichero.close()
            
            #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
            try:
                if self.agflow.lineEdit_4.text() =="":slope="1"
                else:slope= str(int(self.agflow.lineEdit_4.text()))

                if self.agflow.lineEdit_5.text()=="":maxim_d="0.99"
                else:maxim_d=float(self.agflow.lineEdit_5.text())
                if nombre_parametro=="Drainage area \nto concentrated flow": maxim_d=round(param_values[numero_parametro],2)

                if self.agflow.lineEdit_6.text()=="":maxim_pl="300.0"
                else:maxim_pl=float(self.agflow.lineEdit_6.text())
                if nombre_parametro=="Maximum profile length \nuntil deposition": maxim_pl=round(param_values[numero_parametro],2)

                if self.agflow.lineEdit_7.text()=="":maxim_ps="100.0"
                else:maxim_ps=float(self.agflow.lineEdit_7.text())
                if nombre_parametro=="Maximum Profile Slope": maxim_ps=round(param_values[numero_parametro],2)
                
                def funcion_t(numero):
                    if numero==1:
                        return "T"
                    elif numero ==0:
                        return "F"
                
                use=funcion_t(int(self.agflow.checkBox.isChecked()))
                write=funcion_t(int(self.agflow.checkBox_2.isChecked()))
                arc=funcion_t(int(self.agflow.checkBox_3.isChecked()))
                dat=funcion_t(int(self.agflow.checkBox_4.isChecked()))
                use_file=funcion_t(int(self.agflow.checkBox_5.isChecked()))
            
            except:
                iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning,duration = 10)
                return
            
            texto_nuevo = texto.replace("aaaaa",f"    {slope}     {maxim_d}     {maxim_pl}     {maxim_ps}     {use}     {write}     {arc}     {dat}     {use_file}")
            try:
                f = open(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\"+"AGFCNT.inp","w+")
            except:
                iface.messageBar().pushMessage("Select project folder", "Please before creating the agflow data first select de project folder you are going to use",level=Qgis.Warning)
                return 
            f.write(texto_nuevo)
            f.close()
        
        else:
            try:
                direccion#Check if "direccion" and "columna" exist. If they don't, then do anything
                
                df = pd.read_csv(direccion,encoding = "ISO-8859-1",delimiter=",")
                if self.dic_data[nombre_parametro][2]=="All": #si se han elegido todas las filas entonces se cambia en todas las filas
                    df[columna] = [param_values[numero_parametro] for x in range(len(df))]
                else:#si solo se ha elegido una fila entonces se cambia una única fila
                    df[columna].iloc[int(self.dic_data[nombre_parametro][2])] = param_values[numero_parametro]
                #Si está la columna de Cell_ID o Reach ID entonces no tiene que tener formato decimal
                def float_to_str(df,column):
                    #Función para cambiar una columna de float a formato para que cuando se guarde se vea en formato int
                    lista = []
                    for param_values in df[column]:
                        try:
                            lista.append(str(int(param_values)))
                        except:
                            lista.append("")
                    df[column] = lista
                if "Cell_ID" in df.columns: float_to_str(df,"Cell_ID")
                if "Reach_ID" in df.columns: float_to_str(df,"Reach_ID")
                df.to_csv(direccion, index=False, float_format='%.5f')
            except:
                pass
    
    def file_input(self,lineEdit):
        #Metod to go from line edit to the final direction
        
        #First convert from lineEdit to the direction of the folder
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
        
        invertided_dic = {value: key for key, value in master_dict.items()}
        csv_file = invertided_dic[lineEdit]
        
        master_file = self.direccion_sensitivity+f"\\Core_{self.core}"+r"\Processing_inputs\annagnps_master.csv"
        project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")
        
        return Path(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]==csv_file].iloc[0,1])

    
    def change_control_files_pixel(self,i,j):
        #Metod to change control files if sensitivity analysis with pixel size is choosed
        #First with mdt
        df = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\TOPAGNPS.csv",encoding = "ISO-8859-1",delimiter=",")
        df["FILENAME"].iloc[0] = str(self.nombre_mdt_sensitivity+f"_{round(i[j],2)}"+"."+self.extension_mdt_sensitivity)
        df.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\TOPAGNPS.csv", index=False, float_format='%.5f')
        
        #If buffer exist then change name of buffer raster
        if self.fichero_buf_sensitivity!="nan":
            df = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\AGBUF.csv",encoding = "ISO-8859-1",delimiter=",")
            df["BUFFER"].iloc[0] = str(self.nombre_buffer_sensitivity+f"_{round(i[j],2)}"+"."+self.extension_buffer_sensitivity)
            df.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\AGBUF.csv", index=False, float_format='%.5f')
        
        #If vegetation exist then change name of vegetation raster
        if self.fichero_veg_sensitivity!="nan":
            df = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\AGBUF.csv",encoding = "ISO-8859-1",delimiter=",")
            df["VEGETATION"].iloc[0] = str(self.nombre_vegetation_sensitivity+f"_{round(i[j],2)}"+"."+self.extension_vegetation_sensitivity)
            df.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\AGBUF.csv", index=False, float_format='%.5f')
    
    def registrar_numero(self,numero):
        # Definimos la ruta de la carpeta y del archivo
        ruta_carpeta = r"D:\Prueba"
        nombre_archivo = "mensajes.txt"
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        
        # 1. Verificamos si la carpeta existe; si no, la creamos para evitar errores
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada en: {ruta_carpeta}")

        # 2. Abrimos el archivo en modo 'a' (append)
        # Usamos 'with' para que el archivo se cierre automáticamente
        with open(ruta_completa, "a", encoding="utf-8") as archivo:
            # Añadimos el número seguido de un salto de línea
            archivo.write(f"{numero}\n")
        
    
    
    def add_soil_and_management_cell_sensitivity(self):
        """Method to add soil type and management to cell"""
        def fichero(nombre):
            return self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\"+nombre
        #A esta función le das la capa de celdas y la que se superpone (tipo de suelo o uso) y devuelve el diccionario en el que se muestra a cada celda que valor (de suelo o de uso) le corresponde
        def aplicar(fichero_celdas,fichero_superponer, columna_tipo,numero):
            
            numero = str(numero) #esto es porque no deja sobreescribir y tengo que crear otra capa por cada ejecución de sensibilidad
            fichero_cell = fichero_celdas
            fichero_suelo = fichero_superponer
            #Esta función devuelve un diccionario en donde a cada suelo/uso se le asigna un numero entero y luego en la capa (de suelos o uso) a cada suelo/uso se le añade el valor del diccionario
            def create_fid(file_layer):
                layer = file_layer
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
            with qgis_processing_lock: #esto es para que no se use más de un hilo en la paralelización que puede dar problemas en la paralelización. 
                e = processing.run("native:reprojectlayer", 
                    {'INPUT':fichero_suelo,
                    'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg_sensitivity),
                    'OPERATION':'+proj=noop','OUTPUT':fichero(f"reproyect_{self.n}")})
            #Reproyectar celdas al epsg del proyecto
            with qgis_processing_lock:
                a = processing.run("gdal:warpreproject", 
                    {'INPUT':fichero(fichero_cell),
                    'SOURCE_CRS':None,'TARGET_CRS':QgsCoordinateReferenceSystem('{}'.format(self.epsg_sensitivity)),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,
                    'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OPTIONS': 'NUM_THREADS=1','OUTPUT':fichero(f"warp_{self.n}.tif")})
            #Con esto se tiene el diccionario que te asigna para cada suelo/uso un valor numérico
            capa_suelo = QgsVectorLayer(e["OUTPUT"], "temp_suelo", "ogr")
            dic_conv = create_fid(capa_suelo)
            #Rasterizar la capa de suelos
            with qgis_processing_lock:
                processing.run("gdal:rasterize", 
                    {'INPUT':e["OUTPUT"],
                    'FIELD':'id_prueba','BURN':0,'USE_Z':False,'UNITS':1,'WIDTH':self.pixelSizeX,
                    'HEIGHT':self.pixelSizeY,'EXTENT':None,'NODATA':0,'OPTIONS':'','DATA_TYPE':4,'INIT':None,
                    'INVERT':False,'EXTRA':'','OUTPUT':fichero("suelo_ras.tif")})
            #Vectorizar la capa de celdas
            with qgis_processing_lock:
                c = processing.run("gdal:polygonize", 
                    {'INPUT':a["OUTPUT"],
                    'BAND':1,'FIELD':'DN','EIGHT_CONNECTEDNESS':False,'EXTRA':'',
                    'OUTPUT':fichero(f"vec_{self.n}.gpkg")})
                
            r'''c = processing.run("grass7:r.to.vect", {'input':a["OUTPUT"],
                'type':2,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':QgsProcessing.TEMPORARY_OUTPUT,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})'''
            #Corregir geometrías porque luego sino en unión da error 
            with qgis_processing_lock:
                d = processing.run("native:fixgeometries", 
                    {'INPUT':c["OUTPUT"],
                    'OUTPUT':fichero(f"fixed_geometries_{self.n}")})   
            #Se unen las capas de celdas de celdas con las de suelo/uso
            with qgis_processing_lock:
                processing.run("native:union", 
                {'INPUT':d["OUTPUT"],
                'OVERLAY':e["OUTPUT"],
                'OVERLAY_FIELDS_PREFIX':'','OUTPUT':fichero("union_capas{}_{}.gpkg".format(numero,self.n))})
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
            create_attribute("union_capas{}_{}.gpkg".format(numero,self.n),"$area","area_zona")
            #Ahora se ve qué área de suelo/uso es la mayor para cada celda y esa será la que se escoja
            layer = QgsVectorLayer(fichero("union_capas{}_{}.gpkg".format(numero,self.n)),"union")
            tres_valores = []
            valores_unicos_celdas = []
            valores_unicos_suelos=[]
            for f in layer.getFeatures():
                        tres_valores.append((f["DN"],f["id_prueba"],f["area_zona"]))
                        valores_unicos_celdas.append(f["DN"])
                        valores_unicos_suelos.append(f["id_prueba"])
            valores_unicos_celdas = list(np.unique(valores_unicos_celdas))
            valores_unicos_suelos=list(np.unique(valores_unicos_suelos))
            valores_unicos_celdas=[x for x in valores_unicos_celdas if isinstance(x, (int, float))]
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
        annagnps_cell_data = pd.read_csv(fichero("AnnAGNPS_Cell_Data_Section.csv"),encoding = "ISO-8859-1",delimiter=",")
        #Dar error si no se ha elegido ni capa de suelos ni se ha puesto un suelo único
        
        if pd.isna(self.unique_soil_sensitivity):
            if self.fichero_soil_sensitivity=="nan":
                self.end_execution = 1
                self.error_msg = "Error with soil layer\nNo soil layer has been selected"
                return
            #Se aplica el suelo al fichero de cells
            try:
                suelos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_soil_sensitivity,self.column_soil_sensitivity,1)
            except:
                self.end_execution = 1
                self.error_msg = f"Error with soil layer: The DEM and the soil layer have to overlap"
                return
            annagnps_cell_data["Soil_ID"] = [suelos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            
            
            #Se aplica el suelo al fichero de cárcavas efímeras, si existe el archivo PEG.csv
            if path.exists(fichero("PEG.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg_sensitivity),"PEG_Points","memory")
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
                    'COLUMN_PREFIX':'SAMPLE_','OUTPUT':fichero(f"sampling_{self.n}")})
                capa = sampling["OUTPUT"]
                dic_eg = {f["id"].split(" ")[0]:f["SAMPLE_1"] for f in capa.getFeatures()}
                
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    annagnps_eg_data["Soil_ID"]= [dic_conv[x] for x in suelos_eg]
                except:
                    self.end_execution = 1
                    self.error_msg =  "Error soil map\nThe soil type layer may not cover the full extent of the watershed"
                    return
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
                
            
        #Dar error si no se ha elegido ni capa de usos ni se ha puesto un uso único
        if pd.isna(self.unique_use_sensitivity):
            if self.fichero_manag_sensitivity=="nan":
                self.end_execution = 1
                self.error_msg = "Error with soil management\nNo management layer has been selected."
                return
            try:
                manejos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_manag_sensitivity,self.column_use_sensitivity,2)
            except:
                self.end_execution = 1
                self.error_msg = f"Error with management layer: The DEM and the management layer have to overlap"
                return
                
                    
            annagnps_cell_data["Mgmt_Field_ID"] = [manejos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            
            
            #Se aplica el uso al fichero de cárcavas efímeras
            if path.exists(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg_sensitivity),"PEG_Points","memory")
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
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    lista_tipos = []
                    for eg_soil_i,eg_soil_k in enumerate([dic_conv[x] for x in suelos_eg]):
                        if annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="BUFFER" or annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="WETLAND":
                            lista_tipos.append(annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i])
                        else:
                            lista_tipos.append(eg_soil_k)
                    annagnps_eg_data["Mgmt_Field_ID"]= lista_tipos
                except:
                    self.end_execution = 1
                    self.error_msg ="Error soil use map\nThe soil use layer may not cover the full extent of the watershed"
                    return
                    
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
            
        #Si se ha puesto un suelo único entonces se añade a todas las celdas
        if not pd.isna(self.unique_soil_sensitivity):
            annagnps_cell_data["Soil_ID"] =str(self.unique_soil_sensitivity)
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
        #Si se ha puesto un uso único entonces se añade a todas las celdas
        if not pd.isna(self.unique_use_sensitivity):
            annagnps_cell_data["Mgmt_Field_ID"]=str(self.unique_use_sensitivity)
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
    
    
    def create_folder_processing_and_move_files(self):
        """Method to create the preprocessing folders (if they dont exist) and move the input files here"""
        #Move the outputs generated by topagnps to the inputs of annagnps
        names_list = ["AnnAGNPS_Cell_Data_Section.csv","AnnAGNPS_Ephemeral_Gully_Data_Section.csv","AnnAGNPS_Reach_Data_Section.csv","AnnAGNPS_Riparian_Buffer_Data_Section_AgBuf.csv","AnnAGNPS_Wetland_Data_Section.csv"]
        names_in_master = ["Cell Data","Ephemeral Gully Data","Reach Data","Riparian Buffer Data","Wetland Data"]
        master = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\annagnps_master.csv",encoding = "ISO-8859-1",delimiter=",")
        for i in range(len(names_list)):
            #Comprobar si se ejecuta en el proyecto
            if not pd.isna(self.project_df[self.project_df.iloc[:,0]==names_in_master[i]].iloc[0,1]) and os.path.exists(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs\\"+names_list[i]): 
                #Move files
                shutil.copyfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs\\"+names_list[i],self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\watershed\\"+names_list[i])
                #Change annagnps_master
                master[master.iloc[:,0]==names_in_master[i]].iloc[0,1] = f'.\\watershed\\{names_list[i]}'
                master.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\annagnps_master.csv", encoding='utf-8', index=False)
            else: 
                master = master[master.iloc[:,0]!=names_in_master[i]]
                master.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\annagnps_master.csv", encoding='utf-8', index=False)
    

class Calibration_Parallelization(QgsTask):
    def __init__(self, n, core,execute_preprocessing_sensitivity,direccion_sensitivity,dic_data,proximos_inputs,executable_directory,plugin_dir,dic_name_column,inputs, epsg_sensitivity,unique_soil_sensitivity,fichero_soil_sensitivity,column_soil_sensitivity,unique_use_sensitivity,fichero_manag_sensitivity,column_use_sensitivity,project_df,counter_calibration_round):
        super().__init__(f"Tarea_{n}_Carpeta_{core}")
        self.n = n
        self.core = core
        self.execute_preprocessing_sensitivity = execute_preprocessing_sensitivity
        self.direccion_sensitivity = direccion_sensitivity
        self.dic_data = dic_data
        self.proximos_inputs = proximos_inputs
        self.executable_directory = executable_directory
        self.plugin_dir = plugin_dir
        self.dic_name_column = dic_name_column
        self.inputs = inputs
        self.epsg_sensitivity = epsg_sensitivity
        self.unique_soil_sensitivity = unique_soil_sensitivity
        self.fichero_soil_sensitivity = fichero_soil_sensitivity
        self.column_soil_sensitivity = column_soil_sensitivity
        self.unique_use_sensitivity = unique_use_sensitivity
        self.fichero_manag_sensitivity = fichero_manag_sensitivity
        self.column_use_sensitivity = column_use_sensitivity
        self.project_df = project_df
        self.counter_calibration_round = counter_calibration_round
        
        
    def run(self):
        # Ajusta la ruta para que use la carpeta correspondiente al folder_id
        
        self.end_execution = 0
        try:
            self.ejecucion_completa_sensitivity()
        except Exception as e:
            self.error_msg = str(e)
            return False
        if self.end_execution ==1:
            return False
        
        return True
    
    
    def ejecucion_completa_sensitivity(self):
        #Esta función es en donde se ejecuta el modelo
        #EJECUCIÓN DE TOPAGNPS
        if self.execute_preprocessing_sensitivity:
            #Se crea la carpeta de Preprocessing_inputs si no estaba creada. Ahí se meten los inputs y se ejecuta TopAGNPS y luego los outputs se meten a Preprocessing_outputs
            
            #Función para que se le diga el nombre del archivo y te devuelva la dirección completa
            def fichero(nombre):
                return self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\"+nombre
            
            #Dar error si no existe el archivo TOPAGNPS.CSV
            if not os.path.exists(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV"):
                self.error_msg = "Error Input data\nControl file of TopAGNPS, TOPAGNPS.CSV, not found"
                self.end_execution = 1
                return
            #Si el formato de la columna FILENAME no es str entonces dar error
            topagnps_control_file = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS.CSV",encoding = "ISO-8859-1",delimiter=",")
            if type(topagnps_control_file["FILENAME"].iloc[0])!=str:
                self.error_msg ="Error Input data\nPlease select a correct FILENAME in TOPAGNPS.CSV" 
                self.end_execution = 1
                return
            #si se está haciendo un análisis de sensibilidad entonces se cambian los inputs.
            for j,k in enumerate(self.dic_data.keys()):
                self.change_inputs_sensitivity(self.proximos_inputs[self.counter_calibration_round],j,k,spatial =True) #cambio de los inputs espaciales
            #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
            self.time_start_preprocessing = datetime.now()
            #EJECUCIÓN DE TOPAGNPS            
            def main():
                f = open(self.executable_directory+"\\"+f"EjecutarTopagnps_{self.core}.bat","w+")
                linea_uno = "CD /d {}".format(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs")
                linea_dos = r"CALL {}\TopAGNPS_v6.00.a.025_release_64-bit.exe".format(self.executable_directory)
                f.write("{} \n".format(linea_uno))
                f.write("{} \n".format(linea_dos))
                f.close()
            main()
            subprocess.call(self.executable_directory+"\\"+f"EjecutarTopagnps_{self.core}.bat")
            #proc = subprocess.Popen(self.executable_directory+"\\"+"EjecutarTopagnps.bat", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            #stdout, stderr = proc.communicate()
            #If error file of TopAGNPS is opened, then return a error message
            try:
                open(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.csv", "r+") 
            except PermissionError:
                self.error_msg ="Error TopAGNPS","Close TOPAGNPS_err.csv before the start of execution"
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder_sensitivity()
                self.end_execution = 1
                return
            except:
                pass
            #Cuando se eligen coordenadas automáticamente con el plugin primero se ejecuta Topagnps y da error (se ejecuta la primera para poner el reaches en QGIS) osea que no queremos que python salte si hay error en la primera ronda. Queremos que salte python cuando hay error y si se ha seleccionado que no se elige automaticamente. O sino cuando hay error y se ha elegido automáticamente pero la segunda ejecución de Topagnps da error. 
            if os.path.isfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.CSV") and os.path.getsize(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\TOPAGNPS_err.CSV")>0:
                self.end_execution = 1
                error = pd.read_csv(fichero("TOPAGNPS_err.CSV"),encoding = "ISO-8859-1",delimiter=",")
                self.error_msg =f"Error TOPAGNPS\n{error.columns[3]}"
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder_sensitivity()
                #Se abre el archivo de errores
                try:
                    os.startfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs"+"\\TopAGNPS_err.csv")
                except:
                    pass
                #Este return es para parar el codigo
                return
            
            #VALORES DEL TAMAÑO DE PIXEL
            layer = QgsRasterLayer(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\"+topagnps_control_file["FILENAME"].iloc[0],"dednm")
            self.pixelSizeX = round(layer.rasterUnitsPerPixelX(),2)
            self.pixelSizeY = round(layer.rasterUnitsPerPixelY(),2)
            #ASIGNAR LOS VALORES DE SUELO Y MANEJO A AnnAGNPS_Cell_Data_Section.csv
            try:
                self.add_soil_and_management_cell_sensitivity()
            except Exception as e:
                #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
                self.save_files_preprocessing_in_folder_sensitivity()
                self.error_msg =str(e)
                
                error_completo = traceback.format_exc()
                
                
                return
            #Los outputs de TopAGNPS se guardan en Preprocessing_outputs
            self.save_files_preprocessing_in_folder_sensitivity()
            
            #Move the outputs of TopAGNPS to use as inputs of AnnAGNPS 
            self.create_folder_processing_and_move_files()
            
        #EJECUCIÓN DE ANNAGNPS

        #MOVER EL ANNAGNPS.FIL (CREO QUE ES EL CONTROL FILE DE ANNAGNPS) A LA CARPETA DE INPUTS de procesamiento
        shutil.copyfile(self.plugin_dir+"\\Executables"  + "\\" +"AnnAGNPS.fil" ,self.direccion_sensitivity +f"\\Core_{self.core}"+"\\Processing_inputs\\" +"AnnAGNPS.fil")
        #Se cambian los inputs
        for j,k in enumerate(self.dic_data.keys()):
            self.change_inputs_sensitivity(self.proximos_inputs[self.counter_calibration_round],j,k,spatial =False) #cambio de los inptus no espaciales
        
        
        
        #Save the time when this is executed. The files that have been created or modificed after that will be save in Preprocessing_outputs
        self.time_start_processing = datetime.now()
        
        #EJECUCIÓN DE ANNAGNPS
        #os.chdir(self.direccion+"\\"+directory)
        def execute_bat():
           def main():
               f = open(self.executable_directory+"\\"+f"EjecutarAnnAGNPS_{self.core}.bat","w+")
               linea_uno = "CD /d {}".format(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs")
               linea_dos = r"CALL {}\AnnAGNPS_v6.00.r.058_release_64-bit.exe".format(self.executable_directory)
               f.write("{} \n".format(linea_uno))
               f.write("{} \n".format(linea_dos))
               f.close()
           main()
        execute_bat()
        r'''env = os.environ.copy()
        env['PATH'] = f'{self.executable_directory};' + env['PATH']
        command = self.executable_directory+"\\"+"EjecutarAnnAGNPS.bat"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='latin-1', env=env)'''

        subprocess.call(self.executable_directory+"\\"+f"EjecutarAnnAGNPS_{self.core}.bat")

        
                  
        #PONER MENSAJE DE ERROR SI ANNAGNPS FUNCIONA MAL
        time.sleep(1)
        if path.exists(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv"):
            if os.stat(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv").st_size>0:
                self.end_execution =1
                try:
                    text = open(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv", "r")
                    text = ''.join([i for i in text]) 
                    text = text.replace("\"", "/") 
                    texto = text.splitlines()
                    txt = texto[2].split(",")[-1]
                    self.error_msg = f"Error AnnAGNPS\n{txt}"
                except:
                    pass
                
                self.end_execution = 1
                #Se abre el archivo de errores
                r'''try:
                    os.startfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\"+"AnnAGNPS_LOG_Error.csv")
                except:
                    pass'''
                #Este return es para parar el codigo
                return 
        
        #EJECUCIÓN DEL OUTPUT_TABLES
        time.sleep(1)
        shutil.copyfile(self.executable_directory + "\\" +"STEAD.fil" ,self.direccion_sensitivity+f"\\Core_{self.core}" + "\\Processing_inputs\\" +"STEAD.fil")
        os.chdir(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs")
        proc = subprocess.Popen(self.executable_directory + "\\" +"STEAD.exe", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        
        #Los outputs de AnnAGNPS se guardan en Processing_outputs
        self.save_files_processing_in_folder_sensitivity()
    
    
    def save_files_preprocessing_in_folder_sensitivity(self):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Preprocessing_outputs if it doesn´t exist
        carpeta = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        
        
        
        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs")
        carpeta_destino = Path(carpeta)

        for f in carpeta_origen.iterdir():
            try:
                if f.is_file():
                    t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                    if t > self.time_start_preprocessing:
                        shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass
    
    
    def save_files_processing_in_folder_sensitivity(self):
        """Method to save the outputs of topagnps in the folder Preprocessing_outputs"""
        #First create the folder Processing_outputs if it doesn´t exist
        carpeta = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_outputs"
        Path(carpeta).mkdir(parents=True, exist_ok=True)
        

        #Then move the files that were modified or created after the start of the preprocessing
        carpeta_origen = Path(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs")
        carpeta_destino = Path(carpeta)
        
        archivo_excluido = Path(self.direccion_sensitivity+f"\\Core_{self.core}") / "Processing_inputs" / "AnnAGNPS.fil"
        
        for f in carpeta_origen.iterdir():
            try:
                t = datetime.fromtimestamp(max(f.stat().st_ctime, f.stat().st_mtime))
                if t > self.time_start_processing and f != archivo_excluido:
                    shutil.move(str(f), str(carpeta_destino / f.name))
            except:
                pass
    
    
    def change_inputs_sensitivity(self,proximos_inputs,numero_parametro,nombre_parametro,spatial):
        #Metod to change the inputs of sensitivity analysis
        try: #este try es para cuando cuando de error si elige la misma columna pero distintas filas
            if self.dic_name_column[nombre_parametro][0]=="Spatial" and spatial:
                direccion = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs\\"+self.dic_name_column[nombre_parametro][1]
                columna = self.dic_name_column[nombre_parametro][2]
            elif self.dic_name_column[nombre_parametro][0]!="Spatial" and not spatial:
                direccion = self.file_input(self.dic_name_column[nombre_parametro][0])
                columna = self.dic_name_column[nombre_parametro][1]
                
        except KeyError: #misma columna, distintas filas
            if self.dic_name_column[nombre_parametro.split("__")[0]][0]=="Spatial" and spatial:
                direccion = self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs\\"+self.dic_name_column[nombre_parametro.split("__")[0]][1]
                columna = self.dic_name_column[nombre_parametro.split("__")[0]][2]
            elif self.dic_name_column[nombre_parametro.split("__")[0]][0]!="Spatial" and not spatial:
                direccion = self.file_input(self.dic_name_column[nombre_parametro.split("__")[0]][0])
                columna = self.dic_name_column[nombre_parametro.split("__")[0]][1]
            

        if self.dic_name_column[nombre_parametro][1]=="AGFLOW.csv" and spatial:#in the case of agflow the input change is different
            #First we add the data of control files to the dialog. This is important because the rest of the values that are not changed need to be taken from the control file.
            self.asignar_valores_control_dialogo()
            #Then we change the inputs of agflow control file
            fichero = open(self.plugin_dir+r"\Documentos\agflow.inp","r+")
            texto = fichero.read()
            fichero.close()
            
            #Aquí se ponen los parámetros en el texto (el ejemplo) importado y se vuelve a guardar
            try:
                if self.agflow.lineEdit_4.text() =="":slope="1"
                else:slope= str(int(self.agflow.lineEdit_4.text()))

                if self.agflow.lineEdit_5.text()=="":maxim_d="0.99"
                else:maxim_d=float(self.agflow.lineEdit_5.text())
                if nombre_parametro=="Drainage area \nto concentrated flow": maxim_d=round(proximos_inputs[numero_parametro],2)

                if self.agflow.lineEdit_6.text()=="":maxim_pl="300.0"
                else:maxim_pl=float(self.agflow.lineEdit_6.text())
                if nombre_parametro=="Maximum profile length \nuntil deposition": maxim_pl=round(proximos_inputs[numero_parametro],2)

                if self.agflow.lineEdit_7.text()=="":maxim_ps="100.0"
                else:maxim_ps=float(self.agflow.lineEdit_7.text())
                if nombre_parametro=="Maximum Profile Slope": maxim_ps=round(proximos_inputs[numero_parametro],2)
                
                def funcion_t(numero):
                    if numero==1:
                        return "T"
                    elif numero ==0:
                        return "F"
                
                use=funcion_t(int(self.agflow.checkBox.isChecked()))
                write=funcion_t(int(self.agflow.checkBox_2.isChecked()))
                arc=funcion_t(int(self.agflow.checkBox_3.isChecked()))
                dat=funcion_t(int(self.agflow.checkBox_4.isChecked()))
                use_file=funcion_t(int(self.agflow.checkBox_5.isChecked()))
            
            except:
                iface.messageBar().pushMessage("Check the data", "Check that all data have been entered correctly.",level=Qgis.Warning,duration = 10)
                return
            
            texto_nuevo = texto.replace("aaaaa",f"    {slope}     {maxim_d}     {maxim_pl}     {maxim_ps}     {use}     {write}     {arc}     {dat}     {use_file}")
            try:
                f = open(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\"+"AGFCNT.inp","w+")
            except:
                iface.messageBar().pushMessage("Select project folder", "Please before creating the agflow data first select de project folder you are going to use",level=Qgis.Warning)
                return 
            f.write(texto_nuevo)
            f.close()
        
        else:
            try:
                direccion#Check if "direccion" and "columna" exist. If they don't, then do anything
                
                df = pd.read_csv(direccion,encoding = "ISO-8859-1",delimiter=",")
                if self.dic_data[nombre_parametro][2]=="All": #si se han elegido todas las filas entonces se cambia en todas las filas
                    df[columna] = [proximos_inputs[numero_parametro] for x in range(len(df))]
                else:#si solo se ha elegido una fila entonces se cambia una única fila
                    df[columna].iloc[int(self.dic_data[nombre_parametro][2])] = proximos_inputs[numero_parametro]
                #Si está la columna de Cell_ID o Reach ID entonces no tiene que tener formato decimal
                def float_to_str(df,column):
                    #Función para cambiar una columna de float a formato para que cuando se guarde se vea en formato int
                    lista = []
                    for proximos_inputs in df[column]:
                        try:
                            lista.append(str(int(proximos_inputs)))
                        except:
                            lista.append("")
                    df[column] = lista
                if "Cell_ID" in df.columns: float_to_str(df,"Cell_ID")
                if "Reach_ID" in df.columns: float_to_str(df,"Reach_ID")
                df.to_csv(direccion, index=False, float_format='%.5f')
            except:
                pass
    
    def file_input(self,lineEdit):
        #Metod to go from line edit to the final direction
        
        #First convert from lineEdit to the direction of the folder
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
        
        invertided_dic = {value: key for key, value in master_dict.items()}
        csv_file = invertided_dic[lineEdit]
        
        master_file = self.direccion_sensitivity+f"\\Core_{self.core}"+r"\Processing_inputs\annagnps_master.csv"
        project_df = pd.read_csv(master_file,encoding = "ISO-8859-1",delimiter=",")
        
        return Path(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs"+"\\"+project_df[project_df.iloc[:,0]==csv_file].iloc[0,1])

    
    
    def registrar_numero(self,numero):
        # Definimos la ruta de la carpeta y del archivo
        ruta_carpeta = r"D:\Prueba"
        nombre_archivo = "mensajes.txt"
        ruta_completa = os.path.join(ruta_carpeta, nombre_archivo)
        
        # 1. Verificamos si la carpeta existe; si no, la creamos para evitar errores
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)
            print(f"Carpeta creada en: {ruta_carpeta}")

        # 2. Abrimos el archivo en modo 'a' (append)
        # Usamos 'with' para que el archivo se cierre automáticamente
        with open(ruta_completa, "a", encoding="utf-8") as archivo:
            # Añadimos el número seguido de un salto de línea
            archivo.write(f"{numero}\n")
        
    
    
    def add_soil_and_management_cell_sensitivity(self):
        """Method to add soil type and management to cell"""
        def fichero(nombre):
            return self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_inputs"+"\\"+nombre
        #A esta función le das la capa de celdas y la que se superpone (tipo de suelo o uso) y devuelve el diccionario en el que se muestra a cada celda que valor (de suelo o de uso) le corresponde
        def aplicar(fichero_celdas,fichero_superponer, columna_tipo,numero):
            
            numero = str(numero) #esto es porque no deja sobreescribir y tengo que crear otra capa por cada ejecución de sensibilidad
            fichero_cell = fichero_celdas
            fichero_suelo = fichero_superponer
            #Esta función devuelve un diccionario en donde a cada suelo/uso se le asigna un numero entero y luego en la capa (de suelos o uso) a cada suelo/uso se le añade el valor del diccionario
            def create_fid(file_layer):
                layer = file_layer
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
            with qgis_processing_lock: #esto es para que no se use más de un hilo en la paralelización que puede dar problemas en la paralelización. 
                e = processing.run("native:reprojectlayer", 
                    {'INPUT':fichero_suelo,
                    'TARGET_CRS':QgsCoordinateReferenceSystem(self.epsg_sensitivity),
                    'OPERATION':'+proj=noop','OUTPUT':fichero(f"reproyect_{self.n}")})
            #Reproyectar celdas al epsg del proyecto
            with qgis_processing_lock:
                a = processing.run("gdal:warpreproject", 
                    {'INPUT':fichero(fichero_cell),
                    'SOURCE_CRS':None,'TARGET_CRS':QgsCoordinateReferenceSystem('{}'.format(self.epsg_sensitivity)),
                    'RESAMPLING':0,'NODATA':None,'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,
                    'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OPTIONS': 'NUM_THREADS=1','OUTPUT':fichero(f"warp_{self.n}.tif")})
            #Con esto se tiene el diccionario que te asigna para cada suelo/uso un valor numérico
            capa_suelo = QgsVectorLayer(e["OUTPUT"], "temp_suelo", "ogr")
            dic_conv = create_fid(capa_suelo)
            #Rasterizar la capa de suelos
            with qgis_processing_lock:
                processing.run("gdal:rasterize", 
                    {'INPUT':e["OUTPUT"],
                    'FIELD':'id_prueba','BURN':0,'USE_Z':False,'UNITS':1,'WIDTH':self.pixelSizeX,
                    'HEIGHT':self.pixelSizeY,'EXTENT':None,'NODATA':0,'OPTIONS':'','DATA_TYPE':4,'INIT':None,
                    'INVERT':False,'EXTRA':'','OUTPUT':fichero("suelo_ras.tif")})
            #Vectorizar la capa de celdas
            with qgis_processing_lock:
                c = processing.run("gdal:polygonize", 
                    {'INPUT':a["OUTPUT"],
                    'BAND':1,'FIELD':'DN','EIGHT_CONNECTEDNESS':False,'EXTRA':'',
                    'OUTPUT':fichero(f"vec_{self.n}.gpkg")})
                
            r'''c = processing.run("grass7:r.to.vect", {'input':a["OUTPUT"],
                'type':2,'column':'value','-s':False,
                '-v':False,'-z':False,'-b':False,'-t':False,
                'output':QgsProcessing.TEMPORARY_OUTPUT,'GRASS_REGION_PARAMETER':None,
                'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_OUTPUT_TYPE_PARAMETER':0,
                'GRASS_VECTOR_DSCO':'','GRASS_VECTOR_LCO':'',
                'GRASS_VECTOR_EXPORT_NOCAT':False})'''
            #Corregir geometrías porque luego sino en unión da error 
            with qgis_processing_lock:
                d = processing.run("native:fixgeometries", 
                    {'INPUT':c["OUTPUT"],
                    'OUTPUT':fichero(f"fixed_geometries_{self.n}")})   
            #Se unen las capas de celdas de celdas con las de suelo/uso
            with qgis_processing_lock:
                processing.run("native:union", 
                {'INPUT':d["OUTPUT"],
                'OVERLAY':e["OUTPUT"],
                'OVERLAY_FIELDS_PREFIX':'','OUTPUT':fichero("union_capas{}_{}.gpkg".format(numero,self.n))})
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
            create_attribute("union_capas{}_{}.gpkg".format(numero,self.n),"$area","area_zona")
            #Ahora se ve qué área de suelo/uso es la mayor para cada celda y esa será la que se escoja
            layer = QgsVectorLayer(fichero("union_capas{}_{}.gpkg".format(numero,self.n)),"union")
            tres_valores = []
            valores_unicos_celdas = []
            valores_unicos_suelos=[]
            for f in layer.getFeatures():
                        tres_valores.append((f["DN"],f["id_prueba"],f["area_zona"]))
                        valores_unicos_celdas.append(f["DN"])
                        valores_unicos_suelos.append(f["id_prueba"])
            valores_unicos_celdas = list(np.unique(valores_unicos_celdas))
            valores_unicos_suelos=list(np.unique(valores_unicos_suelos))
            valores_unicos_celdas=[x for x in valores_unicos_celdas if isinstance(x, (int, float))]
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
        annagnps_cell_data = pd.read_csv(fichero("AnnAGNPS_Cell_Data_Section.csv"),encoding = "ISO-8859-1",delimiter=",")
        #Dar error si no se ha elegido ni capa de suelos ni se ha puesto un suelo único
        
        if pd.isna(self.unique_soil_sensitivity):
            if self.fichero_soil_sensitivity=="nan":
                self.end_execution = 1
                self.error_msg = "Error with soil layer\nNo soil layer has been selected"
                return
            #Se aplica el suelo al fichero de cells
            try:
                suelos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_soil_sensitivity,self.column_soil_sensitivity,1)
            except:
                self.end_execution = 1
                self.error_msg = f"Error with soil layer: The DEM and the soil layer have to overlap"
                return
            annagnps_cell_data["Soil_ID"] = [suelos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            
            
            #Se aplica el suelo al fichero de cárcavas efímeras, si existe el archivo PEG.csv
            if path.exists(fichero("PEG.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg_sensitivity),"PEG_Points","memory")
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
                    'COLUMN_PREFIX':'SAMPLE_','OUTPUT':fichero(f"sampling_{self.n}")})
                capa = sampling["OUTPUT"]
                dic_eg = {f["id"].split(" ")[0]:f["SAMPLE_1"] for f in capa.getFeatures()}
                
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    annagnps_eg_data["Soil_ID"]= [dic_conv[x] for x in suelos_eg]
                except:
                    self.end_execution = 1
                    self.error_msg =  "Error soil map\nThe soil type layer may not cover the full extent of the watershed"
                    return
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
                
            
        #Dar error si no se ha elegido ni capa de usos ni se ha puesto un uso único
        if pd.isna(self.unique_use_sensitivity):
            if self.fichero_manag_sensitivity=="nan":
                self.end_execution = 1
                self.error_msg = "Error with soil management\nNo management layer has been selected."
                return
            try:
                manejos,dic_conv = aplicar("AnnAGNPS_Cell_IDs.asc",self.fichero_manag_sensitivity,self.column_use_sensitivity,2)
            except:
                self.end_execution = 1
                self.error_msg = f"Error with management layer: The DEM and the management layer have to overlap"
                return
                
                    
            annagnps_cell_data["Mgmt_Field_ID"] = [manejos[annagnps_cell_data["Cell_ID"].iloc[x]] for x in range(len(annagnps_cell_data))]
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
            
            
            #Se aplica el uso al fichero de cárcavas efímeras
            if path.exists(fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv")):
                eg_path = fichero("AnnAGNPS_Ephemeral_Gully_Data_Section.csv") #se obtiene el nombre del archivo al que hay que poner el tipo y manejo de suelo
                summary = pd.read_csv("PEG_Summary.txt",encoding = "ISO-8859-1",delimiter=",")
                def create_layer():
                    layer = QgsVectorLayer("Point?crs={}".format(self.epsg_sensitivity),"PEG_Points","memory")
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
                annagnps_eg_data = pd.read_csv(eg_path,encoding = "ISO-8859-1",delimiter=",")
                suelos_eg = [dic_eg[x] for x in annagnps_eg_data["Gully_ID"]]
                try:
                    lista_tipos = []
                    for eg_soil_i,eg_soil_k in enumerate([dic_conv[x] for x in suelos_eg]):
                        if annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="BUFFER" or annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i]=="WETLAND":
                            lista_tipos.append(annagnps_eg_data["Mgmt_Field_ID"].iloc[eg_soil_i])
                        else:
                            lista_tipos.append(eg_soil_k)
                    annagnps_eg_data["Mgmt_Field_ID"]= lista_tipos
                except:
                    self.end_execution = 1
                    self.error_msg ="Error soil use map\nThe soil use layer may not cover the full extent of the watershed"
                    return
                    
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
                annagnps_eg_data.to_csv(eg_path, index=False, float_format='%.5f')
            
        #Si se ha puesto un suelo único entonces se añade a todas las celdas
        if not pd.isna(self.unique_soil_sensitivity):
            annagnps_cell_data["Soil_ID"] =str(self.unique_soil_sensitivity)
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
        #Si se ha puesto un uso único entonces se añade a todas las celdas
        if not pd.isna(self.unique_use_sensitivity):
            annagnps_cell_data["Mgmt_Field_ID"]=str(self.unique_use_sensitivity)
            annagnps_cell_data.to_csv(fichero('AnnAGNPS_Cell_Data_Section.csv'), index=False, float_format='%.5f')
    
    
    def create_folder_processing_and_move_files(self):
        """Method to create the preprocessing folders (if they dont exist) and move the input files here"""
        #Move the outputs generated by topagnps to the inputs of annagnps
        names_list = ["AnnAGNPS_Cell_Data_Section.csv","AnnAGNPS_Ephemeral_Gully_Data_Section.csv","AnnAGNPS_Reach_Data_Section.csv","AnnAGNPS_Riparian_Buffer_Data_Section_AgBuf.csv","AnnAGNPS_Wetland_Data_Section.csv"]
        names_in_master = ["Cell Data","Ephemeral Gully Data","Reach Data","Riparian Buffer Data","Wetland Data"]
        master = pd.read_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\annagnps_master.csv",encoding = "ISO-8859-1",delimiter=",")
        for i in range(len(names_list)):
            #Comprobar si se ejecuta en el proyecto
            if not pd.isna(self.project_df[self.project_df.iloc[:,0]==names_in_master[i]].iloc[0,1]) and os.path.exists(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs\\"+names_list[i]): 
                #Move files
                shutil.copyfile(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Preprocessing_outputs\\"+names_list[i],self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\watershed\\"+names_list[i])
                #Change annagnps_master
                master[master.iloc[:,0]==names_in_master[i]].iloc[0,1] = f'.\\watershed\\{names_list[i]}'
                master.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\annagnps_master.csv", encoding='utf-8', index=False)
            else: 
                master = master[master.iloc[:,0]!=names_in_master[i]]
                master.to_csv(self.direccion_sensitivity+f"\\Core_{self.core}"+"\\Processing_inputs\\annagnps_master.csv", encoding='utf-8', index=False)