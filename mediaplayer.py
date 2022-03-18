from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QUrl
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QStyle, QSlider, QLabel, \
    QFileDialog, QAction, QShortcut, QFrame
from PyQt5.QtGui import QIcon, QPalette, QColor, QKeySequence
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from ThreadMaker import CameraThread, VoiceThread
from mslider import MSlider
from util import *


class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowTitle("Media Player")
        self.setWindowIcon(QIcon("icons/player.png"))  # https://www.flaticon.com/premium-icon/youtube_2504965

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_selected = False

        videoWidget = QVideoWidget()
        videoWidget.setStyleSheet("background:black;")

        self.shortcut_forward = QShortcut(QKeySequence('Shift+Right'), self)
        self.shortcut_forward.activated.connect(self.forward)
        self.shortcut_forward.setEnabled(False)

        self.shortcut_backward = QShortcut(QKeySequence('Shift+Left'), self)
        self.shortcut_backward.activated.connect(self.backward)
        self.shortcut_backward.setEnabled(False)

        self.shortcut_play = QShortcut(QKeySequence('Space'), self)
        self.shortcut_play.activated.connect(self.play_video)
        self.shortcut_play.setEnabled(False)

        self.shortcut_volup = QShortcut(QKeySequence('Up'), self)
        self.shortcut_volup.activated.connect(self.vol_up)

        self.shortcut_voldown = QShortcut(QKeySequence('Down'), self)
        self.shortcut_voldown.activated.connect(self.vol_down)

        self.openButton = QPushButton("Open Video")
        self.openButton.clicked.connect(self.open_file)
        self.openButton.setIcon(QIcon("icons/open.png"))  # https://www.flaticon.com/free-icon/open_3143203

        self.backwardButton = QPushButton()
        self.backwardButton.setEnabled(False)
        self.backwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.backwardButton.clicked.connect(self.backward)

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.play_video)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.forwardButton = QPushButton()
        self.forwardButton.setEnabled(False)
        self.forwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.forwardButton.clicked.connect(self.forward)

        self.timeCurrentLabel = QLabel("00:00")
        self.timeTotalLabel = QLabel("00:00")

        self.videoSlider = MSlider(Qt.Horizontal)
        self.videoSlider.setRange(0, 0)
        self.videoSlider.sliderMoved.connect(self.mediaPlayer.setPosition)

        self.volumeLabel = QLabel()
        self.volumeLabel.setPixmap(self.style().standardPixmap(QStyle.SP_MediaVolume))

        self.volumeSlider = MSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(50)
        self.volumeSlider.setFixedWidth(100)
        self.volumeSlider.valueChanged.connect(self.mediaPlayer.setVolume)

        self.toggleRightButton = QPushButton()
        self.toggleRightButton.setIcon(
            QIcon("icons/show.png"))  # https://www.flaticon.com/premium-icon/on-button_5683514
        self.toggleRightButton.clicked.connect(self.toggle_right_panel)

        hbox = QHBoxLayout()

        hbox.addWidget(self.openButton)

        hbox.addWidget(self.backwardButton)
        hbox.addWidget(self.playButton)
        hbox.addWidget(self.forwardButton)

        hbox.addWidget(self.timeCurrentLabel)
        hbox.addWidget(self.videoSlider)
        hbox.addWidget(self.timeTotalLabel)

        hbox.addWidget(self.volumeLabel)
        hbox.addWidget(self.volumeSlider)

        hbox.addWidget(self.toggleRightButton)

        hbox.setContentsMargins(20, 20, 20, 30)

        # Right panel for camera and feedback
        self.vboxRight = self.create_right_panel()
        self.vboxRight_visible = True
        self.right_widget_list = self.get_right_frame_widgets()

        self.hboxUp = QHBoxLayout()
        self.hboxUp.addWidget(videoWidget)
        self.hboxUp.addLayout(self.vboxRight)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.hboxUp)
        self.main_layout.addLayout(hbox)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)
        self.showMaximized()

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.maxDuration = 0

        # Media player signals
        self.mediaPlayer.stateChanged.connect(self.mediastate_changed)
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)

        # Camera
        self.camera_on = True
        self.voice_on = False

    def create_right_panel(self):
        vboxRight = QVBoxLayout()

        self.display_width = 350
        self.display_height = 350
        # # Webcam
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
        self.voiceInfoLabel.setStyleSheet("background:white; text-align:center")
        self.voiceInfoLabel.setAlignment(Qt.AlignCenter)
        vboxRight.addWidget(self.voiceInfoLabel)

        self.toggleVoiceButton = QPushButton("Toggle Voice")
        self.toggleVoiceButton.clicked.connect(self.toggle_voice)
        vboxRight.addWidget(self.toggleVoiceButton)

        self.voiceStatusLabel = QLabel()
        self.voiceStatusLabel.setWordWrap(True)
        self.voiceStatusLabel.setStyleSheet("background:white; text-align:center")
        self.voiceStatusLabel.setAlignment(Qt.AlignCenter)
        vboxRight.addWidget(self.voiceStatusLabel)

        self.voiceDetectionLabel = QLabel()
        self.voiceDetectionLabel.setWordWrap(True)
        self.voiceDetectionLabel.setStyleSheet("background:white; text-align:center")
        self.voiceDetectionLabel.setAlignment(Qt.AlignCenter)
        vboxRight.addWidget(self.voiceDetectionLabel)

        # self.voiceThread.start()

        self.rightFrame = QFrame()
        self.rightFrame.setFixedWidth(350)
        self.rightFrame.setStyleSheet("background-color: white;")
        vboxRight.addWidget(self.rightFrame)
        vboxRight.setContentsMargins(0, 0, 10, 0)
        vboxRight.setSpacing(5)
        vboxRight.setStretch(2, 0)

        return vboxRight

    def get_right_frame_widgets(self):
        widget_list = []
        for i in (range(self.vboxRight.count())):
            widget = self.vboxRight.itemAt(i).widget()
            widget_list.append(widget)
        return widget_list

    def toggle_right_panel(self):
        if self.vboxRight_visible:
            for i in reversed(range(self.vboxRight.count())):
                widgetToRemove = self.vboxRight.itemAt(i).widget()
                self.vboxRight.removeWidget(widgetToRemove)
                widgetToRemove.setParent(None)

            self.hboxUp.removeItem(self.vboxRight)
            self.vboxRight_visible = False
            self.toggleRightButton.setIcon(
                QIcon("icons/hide.png"))  # https://www.flaticon.com/premium-icon/off-button_5683501
        else:
            if self.camera_on:
                self.vboxRight.addWidget(self.imageDisplayLabel)
            else:
                self.vboxRight.addWidget(self.image_black_label)
            right_widget_list = self.right_widget_list[1:]  # Remove the first label (already added)
            for i in right_widget_list:
                self.vboxRight.addWidget(i)
            self.hboxUp.addLayout(self.vboxRight)
            self.vboxRight_visible = True
            self.toggleRightButton.setIcon(QIcon("icons/show.png"))

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

    def open_file(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if fileName != '':
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.mediaPlayer.setVolume(self.volumeSlider.value())
            self.playButton.setEnabled(True)
            self.forwardButton.setEnabled(True)
            self.backwardButton.setEnabled(True)

            self.shortcut_forward.setEnabled(True)
            self.shortcut_backward.setEnabled(True)
            self.shortcut_play.setEnabled(True)

            self.video_selected = True

    def play_video(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def duration_changed(self, duration):
        self.videoSlider.setRange(0, duration)
        self.timeTotalLabel.setText(get_time_to_display(duration))
        self.maxDuration = duration

    def position_changed(self, duration):
        self.videoSlider.setValue(duration)
        self.timeCurrentLabel.setText(get_time_to_display(duration))

    def mediastate_changed(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause)
            )
        else:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay)
            )

    def forward(self):
        self.mediaPlayer.setPosition(min(self.mediaPlayer.position() + 10000, self.maxDuration))

    def backward(self):
        self.mediaPlayer.setPosition(max(self.mediaPlayer.position() - 10000, 0))

    def vol_up(self):
        self.volumeSlider.setValue(min(self.volumeSlider.value() + 10, 100))

    def vol_down(self):
        self.volumeSlider.setValue(max(self.volumeSlider.value() - 10, 0))

    # Video showing thread from tutorial at https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1

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
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def detect_audio(self, value):
        """ Get audio from thread """
        # print(value)
        if not self.voice_on:
            return
        if value == "":
            self.voiceDetectionLabel.setText("Sorry, couldn't quite catch that")
        else:
            if self.video_selected:
                self.voiceDetectionLabel.setText(f"Detected \"{value}\"")
                if value in COMMAND_LIST:
                    if value == "forward":
                        self.forward()
                    elif value =="backward":
                        self.backward()
                    elif value == "up" or value == "volume up":
                        self.vol_up()
                    elif value == "down" or value == "volume down":
                        self.vol_down()
                    elif value == "pause":
                        self.mediaPlayer.pause()
                    elif value == "play" or value == "resume":
                        self.mediaPlayer.play()
            else:
                self.voiceDetectionLabel.setText(f"Detected \"{value}\", Please select a video \
                for using voice commands")

    def detect_signal(self, message):
        """ Get audio from thread """
        if not self.voice_on:
            return
        self.voiceStatusLabel.setText(message)
