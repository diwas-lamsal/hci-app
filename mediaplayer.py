import datetime

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QStyle, QSlider, QLabel, \
    QFileDialog, QAction, QShortcut, QFrame
from PyQt5.QtGui import QIcon, QPalette, QColor, QKeySequence
import sys
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

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

    def create_right_panel(self):
        vboxRight = QVBoxLayout()
        self.right_frame = QFrame()
        self.right_frame.setFixedWidth(300)
        self.right_frame.setStyleSheet("background-color: white;")
        vboxRight.addWidget(self.right_frame)
        vboxRight.setContentsMargins(0, 0, 0, 0)
        return vboxRight

    def toggle_right_panel(self):
        if self.vboxRight_visible:
            self.right_frame.setFixedWidth(0)
            self.vboxRight.removeWidget(self.right_frame)
            self.hboxUp.removeItem(self.vboxRight)
            self.vboxRight_visible = False
            self.toggleRightButton.setIcon(
                QIcon("icons/hide.png"))  # https://www.flaticon.com/premium-icon/off-button_5683501
        else:
            self.right_frame.setFixedWidth(300)
            self.vboxRight.addWidget(self.right_frame)
            self.hboxUp.addLayout(self.vboxRight)
            self.vboxRight_visible = True
            self.toggleRightButton.setIcon(QIcon("icons/show.png"))

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


app = QApplication(sys.argv)

window = Window()
window.show()
sys.exit(app.exec())
