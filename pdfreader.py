import os
import sys
import pyautogui
import cv2
import numpy as np
from PyQt6 import QtCore, QtWidgets, QtWebEngineWidgets, QtGui
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QLabel, QPushButton, QFrame

from ThreadMakerPyQt6 import CameraThread, VoiceThread, HoldThread
from util import COMMAND_LIST_PDF

PDFJS = QtCore.QUrl.fromLocalFile('D:\\Qt\\pdfjs-2.13.216-dist\\web\\viewer.html').toString()

class PdfReport(QtWebEngineWidgets.QWebEngineView):
    def load_pdf(self, filename):
        url = QtCore.QUrl.fromLocalFile(filename).toString()
        self.load(QtCore.QUrl.fromUserInput("%s?file=%s" % (PDFJS, url)))

    def sizeHint(self):
        return QtCore.QSize(640, 480)

class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumWidth(1000)
        self.setMinimumHeight(600)
        self.setGeometry(150, 50, 1000, 600)
        self.setWindowTitle("PDF Reader")
        self.showMaximized()
        self.setWindowIcon(QIcon("icons/pdf.png"))  # https://www.flaticon.com/free-icon/pdf_337946

        self.pdf = PdfReport()
        filename = "test.pdf"
        self.pdf.setStyleSheet("background:red")
        self.pdf.load_pdf(filename)

        lay = QtWidgets.QHBoxLayout(self)
        lay.addWidget(self.pdf)

        self.vboxRight = self.create_right_panel()
        lay.addLayout(self.vboxRight)

        # Camera
        self.camera_on = True
        self.voice_on = False


    def create_right_panel(self):
        vboxRight = QVBoxLayout()

        self.display_width = 350
        self.display_height = 350

        # Webcam
        # create the video capture thread
        self.imageDisplayLabel = QLabel(self)
        self.imageDisplayLabel.setStyleSheet("background:white")
        self.imageDisplayLabel.resize(self.display_width, self.display_height)

        self.videoThread = CameraThread()
        # connect its signal to the update_image slot
        self.videoThread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.videoThread.start()
        vboxRight.addWidget(self.imageDisplayLabel)

        self.toggleCameraButton = QPushButton("Toggle Camera")
        self.toggleCameraButton.clicked.connect(self.toggle_camera)
        vboxRight.addWidget(self.toggleCameraButton)

        self.voiceInfoLabel = QLabel("Voice Input is Off")
        self.voiceInfoLabel.setStyleSheet("background:white;")
        self.voiceInfoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vboxRight.addWidget(self.voiceInfoLabel)

        self.toggleVoiceButton = QPushButton("Toggle Voice")
        self.toggleVoiceButton.clicked.connect(self.toggle_voice)
        vboxRight.addWidget(self.toggleVoiceButton)

        self.voiceStatusLabel = QLabel()
        self.voiceStatusLabel.setWordWrap(True)
        self.voiceStatusLabel.setStyleSheet("background:white;")
        self.voiceStatusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vboxRight.addWidget(self.voiceStatusLabel)

        self.voiceDetectionLabel = QLabel()
        self.voiceDetectionLabel.setWordWrap(True)
        self.voiceDetectionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.voiceDetectionLabel.setStyleSheet("background:white; text-align:center")
        vboxRight.addWidget(self.voiceDetectionLabel)

        self.rightFrame = QFrame()
        self.rightFrame.setFixedWidth(350)
        self.rightFrame.setStyleSheet("background-color: white;")
        vboxRight.addWidget(self.rightFrame)
        vboxRight.setContentsMargins(0, 0, 10, 0)
        vboxRight.setSpacing(5)
        vboxRight.setStretch(2, 0)


        return vboxRight

    def get_right_panel_widgets(self):
        widget_list = []
        for i in (range(self.vboxRight.count())):
            widget = self.vboxRight.itemAt(i).widget()
            widget_list.append(widget)
        return widget_list


    def toggle_camera(self):
        if self.camera_on:
            # Black background only displayed when camera is off
            self.image_black_label = QLabel()
            self.image_black_label.resize(self.display_width, self.display_height)
            self.image_black_label.setStyleSheet("background:white")

            # Stop the camera and remove the label that displays the camera
            self.videoThread.stop()
            black_map = QtGui.QPixmap(self.display_width, self.display_height - 90)
            self.vboxRight.removeWidget(self.imageDisplayLabel)
            self.imageDisplayLabel.setParent(None)
            self.vboxRight.insertWidget(0, self.image_black_label)
            self.image_black_label.setPixmap(black_map)
            self.camera_on = False
        else:
            self.vboxRight.removeWidget(self.image_black_label)
            self.image_black_label = None
            self.imageDisplayLabel.setParent(self.image_black_label)
            self.vboxRight.insertWidget(0, self.imageDisplayLabel)
            self.videoThread = CameraThread()
            self.videoThread.change_pixmap_signal.connect(self.update_image)
            self.videoThread.start()
            self.camera_on = True

    def toggle_voice(self):
        if self.voice_on:
            self.voiceInfoLabel.setText("Voice input is off")
            self.voice_on = False
            self.voiceThread.stop()
            del self.voiceThread
            self.voiceStatusLabel.setText("")
            self.voiceDetectionLabel.setText("")
        else:
            self.voiceInfoLabel.setText("Voice input is on")
            self.voice_on = True
            self.voiceThread = VoiceThread()
            self.voiceThread.change_audio_signal.connect(self.detect_audio)
            self.voiceThread.change_receive_signal.connect(self.detect_signal)
            self.voiceThread.start()


    def increase_zoom(self):
        self.pdf.setZoomFactor(self.pdf.zoomFactor() + .5)


    def closeEvent(self, event):
        self.videoThread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.imageDisplayLabel.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.AspectRatioMode.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def detect_audio(self, value):
        """ Get audio from thread """
        # print(value)
        if not self.voice_on:
            return
        if value == "":
            self.voiceDetectionLabel.setText("Sorry, couldn't quite catch that")
        else:
            self.voiceDetectionLabel.setText(f"Detected \"{value}\"")
            if value in COMMAND_LIST_PDF:
                if value == "zoom in" or value=="in":
                    pyautogui.keyDown("ctrl")
                    pyautogui.press("+")
                    pyautogui.keyUp("ctrl")
                elif value == "zoom out" or value == "out":
                    pyautogui.keyDown("ctrl")
                    pyautogui.press("-")
                    pyautogui.keyUp("ctrl")
                elif value == "scroll up" or value == "up":
                    pyautogui.keyDown("up")
                elif value == "scroll down" or value == "down" or value=="continue":
                    print("Reached Here")
                    self.holdThread = HoldThread("down")
                    self.holdThread.start()
                elif value == "stop":
                    self.holdThread.stop()
                    # del self.holdThread
                elif value == "previous":
                    pyautogui.press("left")
                elif value == "next":
                    pyautogui.press("right")


    def detect_signal(self, message):
        """ Get audio from thread """
        if not self.voice_on:
            return
        self.voiceStatusLabel.setText(message)
        # if message == "zoom":
        #     self.increase_zoom()
        # pyautogui.press('down')



app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
