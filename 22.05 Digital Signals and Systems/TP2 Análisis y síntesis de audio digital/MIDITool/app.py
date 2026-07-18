import typing
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import QWidget
import librosa
from UI.UI import Ui_MainWindow
import logging
import os
import sys
import numpy as np
import scipy.signal as sp
import mido
from Utils.Track import Track
from MIDI.Midi import parse_midi_file
from Synth.Synth import Synth, inst_dic
from FX.FXInterface import FXInterface, fx_dict
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.io import wavfile

from Utils.plotWidget import MplCanvas

permited_file_types = "MIDI file (*.mid)"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # type: ignore
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    synthesize = QtCore.pyqtSignal(int, list)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setTextures()
        self.trackItemsArray = []
        self.finalFXList = MainWindow.FXBuilderWidget(
            self.efectosFinalesGroupBox)
        self.finalVolume = 1.0
        self.result: np.ndarray = np.array(0)
        self.currMidiDuration = 0
        self.spectrumPlot = MplCanvas(self.spectrumTab)
        self.spectrumSlider = QtWidgets.QScrollBar(
            QtCore.Qt.Orientation.Horizontal, self.spectrumTab)
        self.spectrumTab.layout().addWidget(self.spectrumSlider)
        self.spectrumSlider.valueChanged.connect(self.scrollSpectrum)
        self.spectrumSlider.setPageStep(1)

        self.Synththread = QtCore.QThread()
        self.worker = MainWindow.Worker()
        self.worker.moveToThread(self.Synththread)
        self.progressBarSintetize.setValue(0)
        self.synthesize.connect(self.worker.run)
        self.worker.started.connect(
            lambda: self.progressBarSintetize.setValue(0))
        self.worker.finished.connect(lambda x: self.Synththread.quit)
        self.worker.finished.connect(self._set_result)
        self.worker.finished.connect(lambda x: self.worker.deleteLater)
        self.worker.progress.connect(self.progressBarSintetize.setValue)
        self.worker.finished.connect(
            lambda x: self.Dir2FileButton.setEnabled(True))
        self.worker.finished.connect(
            lambda x: self.sintetizePushButton.setEnabled(True))
        self.Synththread.finished.connect(self.Synththread.deleteLater)

        self.Synththread.start()

    def setTextures(self):
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./Textures/play.png"),
                       QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButtonPlay.setIcon(icon)
        icon1 = QtGui.QIcon()
        # icon1.addPixmap(QtGui.QPixmap("./Textures/pause.png"),
        #                QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        # self.pushButtonPause.setIcon(icon1)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("./Textures/stop.png"),
                        QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButtonStop.setIcon(icon2)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("./Textures/dowload.png"),
                        QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.pushButton.setIcon(icon3)

    def doSynthesize(self):
        self.Dir2FileButton.setEnabled(False)
        self.sintetizePushButton.setEnabled(False)
        tracks = [
            track.trackData for track in self.trackItemsArray if track.trackData.enabled]
        dur = int(np.ceil(self.currMidiDuration)*44100)
        self.synthesize.emit(dur, tracks)

    def _set_result(self, res: np.ndarray):
        self.result = res * self.finalVolume

    def play(self):
        sd.play(self.result, 44100)

    def save(self):
        wavfile.write("media.wav", data=self.result, rate=44100)

    def stop(self):
        sd.stop()

    def doEspectrogram(self):
        if (self.result.size > 1):
            self.spectrumSlider.setMaximum(
                int(np.ceil(self.result.size/(44100*30)))-1)
            lowerlimit = self.spectrumSlider.value()*44100*30
            upperlimit = self.result.size if self.spectrumSlider.isMaximized() else (
                self.spectrumSlider.value() + 1)*44100*30
            self.spectrumPlot.plot(
                self.result[lowerlimit:upperlimit], self.spectrumSlider.value()*30)

    def scrollSpectrum(self):
        if (self.result.size > 1):
            lowerlimit = self.spectrumSlider.value()*44100*30
            upperlimit = self.result.size if self.spectrumSlider.isMaximized() else (
                self.spectrumSlider.value() + 1)*44100*30
            self.spectrumPlot.plot(
                self.result[lowerlimit:upperlimit], self.spectrumSlider.value()*30)

    def setFinalVolume(self):
        self.finalVolume = self.finalVolumeSlider.value()

    def BrowseFile(self):
        path2file = QtWidgets.QFileDialog.getOpenFileName(
            filter=permited_file_types)
        if path2file[0] == '':
            return
        self.Dir2FileLE.setText(path2file[0])

        for trackItem in self.trackItemsArray:
            self.tracksScrollAreaContents.layout().removeWidget(trackItem)
            trackItem.deleteLater()
        self.trackItemsArray.clear()
        # Load MIDI file
        tracks, tracks_names, dur = parse_midi_file(path2file[0])
        self.currMidiDuration = dur
        # logging.debug(mid.tracks[1])
        for index, track in enumerate(tracks):
            self.trackItemsArray.append(
                MainWindow.TrackItem(self.tracksScrollAreaContents, index, trackData=track,
                                     trackName=tracks_names[index]))
            self.trackItemsArray[index].enableCheckBox.stateChanged.connect(
                self.trackItemsArray[index].enableCheckBoxUpdate)
            self.trackItemsArray[index].modButton.clicked.connect(
                self.trackItemsArray[index].trackEdit)

    class Worker(QtCore.QObject):
        started = QtCore.pyqtSignal()
        finished = QtCore.pyqtSignal(np.ndarray)
        progress = QtCore.pyqtSignal(int)

        @QtCore.pyqtSlot(int, list)
        def run(self, res_size, tracks):
            self.started.emit()
            """Long-running task."""
            result = np.zeros(res_size)
            for i, track in enumerate(tracks):
                if track.enabled:
                    parRes = track.synth.synthetize(
                        track=track.data)
                    parRes = FXInterface.applyFX(parRes, track.fx)
                    result[:len(parRes)] += parRes/len(tracks)
                    self.progress.emit(
                        int((i + 1)/len(tracks)*100))
            self.finished.emit(result)

    class TrackItem(QtWidgets.QWidget):  # Qwidgets es la herencia, el papi

        # Constructor. Variable: DataType
        def __init__(self, parent: QtWidgets.QWidget, index: int, trackData: list, trackName):
            # Constructor de Widget. Super().init construye todas las clases padres
            self.index = index  # Nose si hace falta, en principio lo dejo
            self.track_name = trackName
            super().__init__(parent)
            parent.layout().addWidget(self)
            self.setLayout(QtWidgets.QHBoxLayout())
            self.trackLabel = QtWidgets.QLabel(
                f"Track: {self.track_name}", parent=self)
            self.modButton = QtWidgets.QPushButton("Modificar", parent=self)
            self.enableCheckBox = QtWidgets.QCheckBox("Agregar", parent=self)
            self.enableCheckBox.setChecked(True)
            self.layout().addWidget(self.trackLabel)
            self.layout().addWidget(self.modButton)
            self.layout().addWidget(self.enableCheckBox)
            self.trackData = Track(
                data=trackData, enabled=True, synth=Synth(), fx=[])

        def enableCheckBoxUpdate(self):
            self.trackData.enabled = self.enableCheckBox.isChecked()

        def trackEdit(self):
            fxadddiag = MainWindow.TrackEditPopUp(self.trackData)
            if fxadddiag.exec():
                self.trackData = fxadddiag.getData()

    class FXBuilderWidget(QtWidgets.QListWidget):
        def __init__(self, parent: QWidget, previous_data=None):
            super().__init__(parent)
            parent.layout().addWidget(self)
            self.additem = QtWidgets.QListWidgetItem()
            self.additembutton = QtWidgets.QPushButton("+")
            self.addItem(self.additem)
            self.setItemWidget(self.additem, self.additembutton)
            self.additembutton.clicked.connect(self.addFX)
            self.fxitems = []
            if isinstance(previous_data, list):
                self.addprevFX(previous_data)

        def addFX(self):
            fxadddiag = MainWindow.FXBuilderWidget.FXAddDialog()
            if fxadddiag.exec():
                fxdata = fxadddiag.getData()
                aux = QtWidgets.QListWidgetItem()
                self.fxitems.append(
                    MainWindow.FXBuilderWidget.FXDataWidget(aux, fxdata))
                self.fxitems[-1].remove.connect(self.removeFX)
                aux.setSizeHint(self.fxitems[-1].sizeHint())
                self.addItem(aux)
                self.setItemWidget(aux, self.fxitems[-1])

        def addprevFX(self, prevfxdata):
            for fxdata in prevfxdata:
                aux = QtWidgets.QListWidgetItem()
                self.fxitems.append(
                    MainWindow.FXBuilderWidget.FXDataWidget(aux, fxdata))
                self.fxitems[-1].remove.connect(self.removeFX)
                aux.setSizeHint(self.fxitems[-1].sizeHint())
                self.addItem(aux)
                self.setItemWidget(aux, self.fxitems[-1])

        def removeFX(self, item):
            index = self.indexFromItem(item).row() - 1
            self.removeItemWidget(item)
            self.fxitems[index].deleteLater()
            self.fxitems.pop(index)
            self.takeItem(index+1)

        def getData(self):
            return [item.getData() for item in self.fxitems]

        class FXDataWidget(QtWidgets.QWidget):

            remove = QtCore.pyqtSignal(
                QtWidgets.QListWidgetItem, name="removeClicked")

            def __init__(self, parent: QWidget, data) -> None:
                super().__init__(parent=None)
                self.setLayout(QtWidgets.QGridLayout())
                self.data = data
                self.parentitem = parent
                self.deleteButton = QtWidgets.QPushButton("-")
                self.deleteButton.setMaximumWidth(20)
                self.deleteButton.clicked.connect(self.removeClicked)
                self.fxname = QtWidgets.QLabel(data[0], parent=self)
                self.layout().addWidget(self.fxname, 0, 1)
                self.layout().addWidget(self.deleteButton, 0, 0)
                self.infolabels = []
                for i, info2get in enumerate(fx_dict[data[0]][1:]):
                    paramlabel = QtWidgets.QLabel(
                        f"{info2get[0]}: {data[1][i]}", parent=self)
                    self.layout().addWidget(paramlabel, 1 + i//2, 1 + i % 2)
                    self.infolabels.append(paramlabel)

            def removeClicked(self):
                self.remove.emit(self.parentitem)

            def getData(self):
                return self.data

        class FXAddDialog(QtWidgets.QDialog):
            input_types = {float: QtWidgets.QDoubleSpinBox,
                           int: QtWidgets.QSpinBox}

            def __init__(self, parent=None):
                QtWidgets.QDialog.__init__(self, parent=parent)
                self.setLayout(QtWidgets.QGridLayout())
                self.setWindowTitle("Seleccionar efecto")

                QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel

                self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.FXCombobox = QtWidgets.QComboBox()
                self.layout().addWidget(self.FXCombobox, 0, 0)
                self.FXCombobox.addItems(list(fx_dict.keys()))
                self.FXCombobox.currentIndexChanged['int'].connect(
                    self.changeInputData)
                self.inputWidgets = []
                self.fxdata = []
                self.FXCombobox.setCurrentIndex(0)
                self.changeInputData(0)

            def changeInputData(self, index):
                for label, inputbox in self.inputWidgets:
                    self.layout().removeWidget(label)
                    self.layout().removeWidget(inputbox)
                    label.deleteLater()
                    inputbox.deleteLater()

                self.inputWidgets.clear()
                self.fxdata.clear()
                self.layout().removeWidget(self.buttonBox)
                for i, info2get in enumerate(fx_dict[self.FXCombobox.currentText()][1:]):
                    self.fxdata.append(0)
                    label = QtWidgets.QLabel(info2get[0], parent=self)
                    inputbox = self.input_types[type(info2get[1])](parent=self)
                    inputbox.setMaximum(1 if isinstance(
                        info2get[1], float) else 1000)
                    inputbox.setMinimum(0)
                    inputbox.setValue(info2get[1])
                    if isinstance(info2get[1], float):
                        inputbox.setSingleStep(0.01)
                    inputbox.valueChanged.connect(self.updateData)
                    self.layout().addWidget(label, 1 + i//2, 2*(i % 2))
                    self.layout().addWidget(inputbox, 1 + i//2, 2*(i % 2) + 1)
                    self.inputWidgets.append((label, inputbox))
                butt_row = (len(
                    fx_dict[self.FXCombobox.currentText()][1:])-1)//2 + 2
                self.layout().addWidget(self.buttonBox, butt_row, 0)
                self.updateData(0)

            def updateData(self, data):
                for i, input in enumerate(self.inputWidgets):
                    self.fxdata[i] = input[1].value()

            def getData(self):
                return (self.FXCombobox.currentText(), self.fxdata)

    class TrackEditPopUp(QtWidgets.QDialog):

        def __init__(self, previous_data: Track, parent=None):
            QtWidgets.QDialog.__init__(self, parent=parent)
            self.auxTrackData = previous_data
            self.setLayout(QtWidgets.QGridLayout())
            self.setWindowTitle("Modificar el track")
            self.finalFXList = MainWindow.FXBuilderWidget(self,
                                                          self.auxTrackData.fx)

            self.instrumentsComboBox = QtWidgets.QComboBox(parent=self)
            self.layout().addWidget(self.instrumentsComboBox)
            self.instrumentsComboBox.addItems(inst_dic.keys())
            self.instrumentsComboBox.setCurrentText(
                previous_data.synth.instrument)

            self.labelVolume = QtWidgets.QLabel(parent=self)
            self.layout().addWidget(self.labelVolume)
            self.labelVolume.setText("Volumen")
            self.volumeTrackSlider = QtWidgets.QSlider(self)
            self.layout().addWidget(self.volumeTrackSlider)
            self.volumeTrackSlider.setOrientation(
                QtCore.Qt.Orientation.Horizontal)
            self.volumeTrackSlider.setMinimum(0)
            self.volumeTrackSlider.setMaximum(100)
            self.volumeTrackSlider.setValue(int(self.auxTrackData.synth.volume * 100)
                                            )

            QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)
            self.layout().addWidget(self.buttonBox)

        def getData(self):
            self.auxTrackData.fx = self.finalFXList.getData()
            self.auxTrackData.synth.instrument = self.instrumentsComboBox.currentText()
            self.auxTrackData.synth.volume = self.volumeTrackSlider.value() / 100
            return self.auxTrackData
