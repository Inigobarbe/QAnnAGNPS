# -*- coding: utf-8 -*-
"""Live progress dialog for the calibration run: shows how many parallel executions have
finished out of how many are planned, the objective metric of the last finished execution and
the best one found so far, and a button to stop the calibration early."""

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtCore import Qt, pyqtSignal


class CalibrationProgressDialog(QtWidgets.QDialog):

    stop_requested = pyqtSignal()

    def __init__(self, parent=None):
        super(CalibrationProgressDialog, self).__init__(parent)
        self.setWindowTitle("Calibration progress")
        self.setMinimumWidth(420)
        self.setWindowModality(Qt.NonModal)
        #Each parallel AnnAGNPS/TopAGNPS execution opens its own console window, which can end up
        #covering this dialog after it's shown. Keep it on top of every other window (including
        #those native console windows) so it stays visible for the whole calibration run.
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #eef1f4;
            }
            QLabel {
                color: #2c3e50;
            }
            QLabel#status {
                color: #55606b;
                font-style: italic;
            }
            QProgressBar {
                background-color: #ffffff;
                border: 1px solid #d8dee4;
                border-radius: 6px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3f6ea5;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #c0392b;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #a5301f;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)

        title = QtWidgets.QLabel("Calibrating…", self)
        bold_font = title.font()
        bold_font.setBold(True)
        bold_font.setPointSize(bold_font.pointSize()+1)
        title.setFont(bold_font)
        layout.addWidget(title)

        self.status_label = QtWidgets.QLabel("Starting calibration...", self)
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.executions_label = QtWidgets.QLabel("Execution 0 / 0", self)
        layout.addWidget(self.executions_label)

        self.running_label = QtWidgets.QLabel("Running now: 0", self)
        layout.addWidget(self.running_label)

        separator = QtWidgets.QFrame(self)
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("color: #d8dee4;")
        layout.addWidget(separator)

        self.metric_label = QtWidgets.QLabel("Objective metric: -", self)
        layout.addWidget(self.metric_label)

        self.last_label = QtWidgets.QLabel("Last result: -", self)
        layout.addWidget(self.last_label)

        self.best_label = QtWidgets.QLabel("Best result so far: -", self)
        best_font = self.best_label.font()
        best_font.setBold(True)
        self.best_label.setFont(best_font)
        layout.addWidget(self.best_label)

        self.stop_button = QtWidgets.QPushButton("Stop calibration", self)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        layout.addWidget(self.stop_button, alignment=Qt.AlignRight)


    def set_status(self,text):
        """Update the free-text status line (e.g. "Moving files to the working directory...")"""
        self.status_label.setText(text)


    def update_progress(self,completed,total,active,metric_name,last_value,best_value):
        """Update the progress bar and the execution/metric labels"""
        self.status_label.setText("Running AnnAGNPS executions...")
        self.progress_bar.setMaximum(max(total,1))
        self.progress_bar.setValue(min(completed,total))
        self.executions_label.setText(f"Execution {completed} / {total}")
        self.running_label.setText(f"Running now: {active}")
        self.metric_label.setText(f"Objective metric: {metric_name}")
        self.last_label.setText(f"Last result: {last_value:.4f}" if last_value is not None else "Last result: -")
        self.best_label.setText(f"Best result so far: {best_value:.4f}" if best_value is not None else "Best result so far: -")


    def disable_stop(self):
        """Disable the stop button (e.g. once the calibration is already finishing up)"""
        self.stop_button.setEnabled(False)
