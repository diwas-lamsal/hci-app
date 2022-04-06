# GLOBAL:
import datetime
import math
import time
import typing

from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget

import config

COMMAND_LIST = ['forward', 'backward', 'volume up', 'volume down', 'up', 'down', 'pause', 'play']
COMMAND_LIST_PDF = ['zoom in', 'in', 'zoom out', 'out', 'scroll up', 'scroll down', 'up', 'down', 'continue', 'next',
                    'previous']

def get_time_to_display(duration):
    # https://stackoverflow.com/questions/775049/how-do-i-convert-seconds-to-hours-minutes-and-seconds
    seconds = int(duration / 1000.0)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h == 0:
        total_duration = f"{str(m).zfill(2)}:{str(s).zfill(2)}"
    else:
        total_duration = f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}"
    return total_duration


# FOR FACE GESTURES

import pag as pag
from imutils import face_utils
from matplotlib import pyplot as plt

import numpy as np
import pyautogui as pyag
import imutils
import dlib
import cv2

import numpy as np


# Returns EAR given eye landmarks
def eye_aspect_ratio(eye):
    # Compute the euclidean distances between the two sets of
    # vertical eye landmarks (x, y)-coordinates
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])

    # Compute the euclidean distance between the horizontal
    # eye landmark (x, y)-coordinates
    C = np.linalg.norm(eye[0] - eye[3])

    # Compute the eye aspect ratio
    ear = (A + B) / (2.0 * C)

    # Return the eye aspect ratio
    return ear


# Returns MAR given eye landmarks
def mouth_aspect_ratio(mouth):
    # Compute the euclidean distances between the three sets
    # of vertical mouth landmarks (x, y)-coordinates
    A = np.linalg.norm(mouth[13] - mouth[19])
    B = np.linalg.norm(mouth[14] - mouth[18])
    C = np.linalg.norm(mouth[15] - mouth[17])

    # Compute the euclidean distance between the horizontal
    # mouth landmarks (x, y)-coordinates
    D = np.linalg.norm(mouth[12] - mouth[16])

    # Compute the mouth aspect ratio
    mar = (A + B + C) / (2 * D)

    # Return the mouth aspect ratio
    return mar


# Return direction given the nose and anchor points.
def direction(nose_point, anchor_point, w, h, multiple=1):
    nx, ny = nose_point
    x, y = anchor_point

    if nx > x + multiple * w:
        return 'right'
    elif nx < x - multiple * w:
        return 'left'

    if ny > y + multiple * h:
        return 'down'
    elif ny < y - multiple * h:
        return 'up'

    return 'none'


# Thresholds and consecutive frame length for triggering the mouse action.
MOUTH_AR_THRESH = 0.6
MOUTH_AR_CONSECUTIVE_FRAMES = 15
EYE_AR_THRESH = 0.19
EYE_AR_CONSECUTIVE_FRAMES = 15
WINK_AR_DIFF_THRESH = 0.04
WINK_AR_CLOSE_THRESH = 0.19
WINK_CONSECUTIVE_FRAMES = 10

MAR_TIMER = None

# Initialize the frame counters for each action as well as
# booleans used to indicate if action is performed or not
MOUTH_COUNTER = 0
EYE_COUNTER = 0
WINK_COUNTER = 0
INPUT_MODE = False
EYE_CLICK = False
LEFT_WINK = False
RIGHT_WINK = False
SCROLL_MODE = False
ANCHOR_POINT = (300, 250)
WHITE_COLOR = (255, 255, 255)
YELLOW_COLOR = (0, 255, 255)
RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (255, 0, 0)
BLACK_COLOR = (0, 0, 0)

# Initialize Dlib's face detector (HOG-based) and then create
# the facial landmark predictor
shape_predictor = "shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(shape_predictor)

# Grab the indexes of the facial landmarks for the left and
# right eye, nose and mouth respectively
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(nStart, nEnd) = face_utils.FACIAL_LANDMARKS_IDXS["nose"]
(mStart, mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]
(lbStart, lbEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]
(rbStart, rbEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]

ACCELERATION = 1
ACCELERATION_TIMER = 0
RESET_ACCELERATION_TIMER = 0

# For Eyebrow
INITIAL_EYEBROW_ASPECT_RATIO = None

def return_processed_image(cv_img):
    global MAR_TIMER
    global WINK_COUNTER
    global ACCELERATION
    global ACCELERATION_TIMER
    global RESET_ACCELERATION_TIMER
    global INITIAL_EYEBROW_ASPECT_RATIO

    frame = cv_img
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)
    if len(rects) > 0:
        rect = rects[0]
    else:
        return frame

    # If face is detected

    # Determine the facial landmarks for the face region, then
    # convert the facial landmark (x, y)-coordinates to a NumPy
    # array
    shape = predictor(gray, rect)
    shape = face_utils.shape_to_np(shape)

    # Extract the left and right eye coordinates, then use the
    # coordinates to compute the eye aspect ratio for both eyes
    mouth = shape[mStart:mEnd]
    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]
    nose = shape[nStart:nEnd]

    # Because I flipped the frame, left is right, right is left.
    temp = leftEye
    leftEye = rightEye
    rightEye = temp

    # Average the mouth aspect ratio together for both eyes
    mar = mouth_aspect_ratio(mouth)
    leftEAR = eye_aspect_ratio(leftEye)
    rightEAR = eye_aspect_ratio(rightEye)
    ear = (leftEAR + rightEAR) / 2.0
    diff_ear = np.abs(leftEAR - rightEAR)

    nose_point = (nose[3, 0], nose[3, 1])

    # Compute the convex hull for the left and right eye, then
    # visualize each of the eyes
    mouthHull = cv2.convexHull(mouth)
    leftEyeHull = cv2.convexHull(leftEye)
    rightEyeHull = cv2.convexHull(rightEye)
    cv2.drawContours(frame, [mouthHull], -1, YELLOW_COLOR, 1)
    cv2.drawContours(frame, [leftEyeHull], -1, YELLOW_COLOR, 1)
    cv2.drawContours(frame, [rightEyeHull], -1, YELLOW_COLOR, 1)

    for (x, y) in np.concatenate((mouth, leftEye, rightEye), axis=0):
        cv2.circle(frame, (x, y), 2, GREEN_COLOR, -1)

    gesture_mode = config.get_gesture_mode()

    if gesture_mode == 'head':
        cv2.putText(frame, "READING INPUT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED_COLOR, 2)
        x, y = ANCHOR_POINT
        nx, ny = nose_point
        w, h = 80, 45
        multiple = 1
        cv2.rectangle(frame, (x - w, y - h), (x + w, y + h), GREEN_COLOR, 2)
        cv2.line(frame, ANCHOR_POINT, nose_point, BLUE_COLOR, 2)

        dir = direction(nose_point, ANCHOR_POINT, w, h)
        cv2.putText(frame, dir.upper(), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED_COLOR, 2)
        if dir == 'right':
            set_acceleration()
            findMainWindow().forward(ACCELERATION)
        elif dir == 'left':
            set_acceleration()
            findMainWindow().backward(ACCELERATION)
        elif dir == 'up':
            findMainWindow().vol_up()
        elif dir == 'down':
            findMainWindow().vol_down()

        if dir != 'left' and dir != 'right':
            ACCELERATION = 1

    # IF the mouth aspect ratio (opening of mouth) is more than threshold, pause or play the video
    if mar > MOUTH_AR_THRESH:
        if MAR_TIMER == None:
            MAR_TIMER = datetime.datetime.now()
            findMainWindow().play_video()  # Pause or play the video depending on current state
        # pyag.press('space') # Pressing space does the same thing, but better to use the window's function

    # Delay successive detections by one second
    if MAR_TIMER != None and datetime.datetime.now() > MAR_TIMER + datetime.timedelta(seconds=1):
        MAR_TIMER = None


    if gesture_mode == 'face':
        # Detecting wink
        if diff_ear > WINK_AR_DIFF_THRESH:
            if leftEAR < rightEAR:
                if leftEAR < EYE_AR_THRESH:
                    set_acceleration(acc_increment=4)
                    findMainWindow().backward(ACCELERATION)

            elif leftEAR > rightEAR:
                if rightEAR < EYE_AR_THRESH:
                    set_acceleration(acc_increment=4)
                    findMainWindow().forward(ACCELERATION)

        # Reset acceleration.
        if diff_ear < WINK_AR_DIFF_THRESH:
            #  or (diff_ear > WINK_AR_DIFF_THRESH and leftEAR > EYE_AR_THRESH and rightEAR > EYE_AR_THRESH)
            if RESET_ACCELERATION_TIMER == 0:
                RESET_ACCELERATION_TIMER = datetime.datetime.now()
            if isinstance(RESET_ACCELERATION_TIMER,datetime.datetime):
                if datetime.datetime.now() > RESET_ACCELERATION_TIMER + datetime.timedelta(seconds=1):
                    ACCELERATION = 1
                    RESET_ACCELERATION_TIMER = 0


        # Detecting eyebrow
        rightEyeBrow = shape[rbStart:rbEnd]
        leftEyeBrow = shape[lbStart:lbEnd]

        x = [p[0][0] for p in leftEyeHull]
        y = [p[0][1] for p in leftEyeHull]
        centroid_left_eye = (sum(x) / len(leftEyeHull), sum(y) / len(leftEyeHull))

        x = [p[0][0] for p in rightEyeHull]
        y = [p[0][1] for p in rightEyeHull]
        centroid_right_eye = (sum(x) / len(rightEyeHull), sum(y) / len(rightEyeHull))

        centroid_left_eye = (int(centroid_left_eye[0]), int(centroid_left_eye[1]))
        centroid_right_eye = (int(centroid_right_eye[0]), int(centroid_right_eye[1]))

        temp = leftEyeBrow
        leftEyeBrow = rightEyeBrow
        rightEyeBrow = temp

        lefteyebrowhull = cv2.convexHull(leftEyeBrow)
        righteyebrowhull = cv2.convexHull(rightEyeBrow)

        x = [p[0][0] for p in lefteyebrowhull]
        y = [p[0][1] for p in lefteyebrowhull]
        centroid_left_eyebrow = (sum(x) / len(lefteyebrowhull), sum(y) / len(lefteyebrowhull))

        x = [p[0][0] for p in righteyebrowhull]
        y = [p[0][1] for p in righteyebrowhull]
        centroid_right_eyebrow = (sum(x) / len(righteyebrowhull), sum(y) / len(righteyebrowhull))

        centroid_left_eyebrow = (int(centroid_left_eyebrow[0]), int(centroid_left_eyebrow[1]))
        centroid_right_eyebrow = (int(centroid_right_eyebrow[0]), int(centroid_right_eyebrow[1]))

        distance_left = distance(centroid_left_eye, centroid_left_eyebrow)
        distance_right = distance(centroid_right_eye, centroid_right_eyebrow)

        distance_top = distance(centroid_left_eyebrow, centroid_right_eyebrow)
        distance_bottom = distance(centroid_left_eye, centroid_right_eye)

        height = distance_left if distance_left > distance_right else distance_right
        width = distance_top if distance_top > distance_bottom else distance_bottom

        aspect_ratio = height / width
        if INITIAL_EYEBROW_ASPECT_RATIO == None:
            INITIAL_EYEBROW_ASPECT_RATIO = aspect_ratio

        if aspect_ratio > INITIAL_EYEBROW_ASPECT_RATIO + 0.07:
            findMainWindow().vol_up(5)
        if aspect_ratio < INITIAL_EYEBROW_ASPECT_RATIO - 0.05:
            findMainWindow().vol_down(5)

    return cv_img


# https://forum.qt.io/topic/84824/accessing-the-main-window-from-python/2
def findMainWindow() -> typing.Union[QWidget, None]:
    # Global function to find the (open) QMainWindow in application
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QWidget):
            return widget
    return None


def set_acceleration(acc_increment=2):
    global ACCELERATION_TIMER, ACCELERATION, RESET_ACCELERATION_TIMER
    if ACCELERATION_TIMER == 0:
        ACCELERATION_TIMER = datetime.datetime.now()
    elif datetime.datetime.now() > ACCELERATION_TIMER + datetime.timedelta(seconds=0.5):
        ACCELERATION = ACCELERATION + acc_increment
        ACCELERATION_TIMER = 0

    if isinstance(RESET_ACCELERATION_TIMER, datetime.datetime):
        RESET_ACCELERATION_TIMER = datetime.datetime.now()


def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def distance(p1,p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p2[1] - p1[1]) ** 2)
