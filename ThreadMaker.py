import cv2
import numpy as np
import speech_recognition as sr


# https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtCore

from util import COMMAND_LIST, return_processed_image


class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                cv_img = cv2.flip(cv_img, 1)

                try:
                    cv_img = return_processed_image(cv_img)
                except:
                    print("Error while using gestures")

                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class VoiceWorker(QtCore.QObject):
    textChanged = QtCore.pyqtSignal(str)

    @QtCore.pyqtSlot()
    def task(self):
        r = sr.Recognizer()
        m = sr.Microphone()

        while True:
            print("Say somethig!")
            with m as source:
                r.adjust_for_ambient_noise(source)  # reduce noise
                audio = r.listen(source)
                print("Got it! Now to recognize it...")
                try:
                    value = r.recognize_google(audio, language = 'pt', show_all=True)
                    self.textChanged.emit(value)
                    print("You said: {}".format(value))
                except Exception as e:
                    print(e)

# https://stackoverflow.com/questions/56200533/when-i-try-to-run-speech-recognition-in-pyqt5-program-is-crashed

class VoiceThread(QThread):
    change_audio_signal = pyqtSignal(str)
    change_receive_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # capture from web cam
        r = sr.Recognizer()
        m = sr.Microphone()
        while self._run_flag:
            self.change_receive_signal.emit("Say something!")
            with m as source:
                r.adjust_for_ambient_noise(source)  # reduce noise
                audio = r.listen(source)
                self.change_receive_signal.emit("Trying to recognize...")
                try:
                    value_all = r.recognize_google(audio, language='en-EN', show_all=True)
                    if len(value_all)>0:
                        value = value_all['alternative'][0]['transcript']
                        for i in value_all['alternative']:
                            if(i['transcript'] in COMMAND_LIST):
                                value = i['transcript']
                    else:
                        value = ""
                    self.change_audio_signal.emit(value)
                except Exception as e:
                    print(e)

    def stop(self):
        """Ends the thread"""
        self._run_flag = False



