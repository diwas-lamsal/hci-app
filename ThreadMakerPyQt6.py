import cv2
import numpy as np
import pyautogui
import speech_recognition as sr

# https://gist.github.com/docPhil99/ca4da12c9d6f29b9cea137b617c7b8b1
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6 import QtCore

from util import COMMAND_LIST, COMMAND_LIST_PDF


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


                
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


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
                    value_all = r.recognize_google(audio, language='en-GB', show_all=True)
                    if len(value_all)>0:
                        value = value_all['alternative'][0]['transcript']
                        for i in value_all['alternative']:
                            if(i['transcript'] in COMMAND_LIST_PDF):
                                value = i['transcript']
                    else:
                        value = ""
                    self.change_audio_signal.emit(value)
                except Exception as e:
                    print(e)

    def stop(self):
        """Ends the thread"""
        self._run_flag = False


class HoldThread(QThread):
    def __init__(self, key_to_press):
        super().__init__()
        self._run_flag = True
        self.key_to_press = key_to_press

    def run(self):
        while self._run_flag:
            pyautogui.keyDown(self.key_to_press)

    def stop(self):
        """Ends the thread"""
        self._run_flag = False
        self.wait()

