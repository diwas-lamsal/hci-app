import math

from imutils import face_utils
from utils import *
import numpy as np
import pyautogui as pyag
import imutils
import dlib
import cv2

# Thresholds and consecutive frame length for triggering the mouse action.
MOUTH_AR_THRESH = 0.6
MOUTH_AR_CONSECUTIVE_FRAMES = 15
EYE_AR_THRESH = 0.19
EYE_AR_CONSECUTIVE_FRAMES = 15
WINK_AR_DIFF_THRESH = 0.04
WINK_AR_CLOSE_THRESH = 0.19
WINK_CONSECUTIVE_FRAMES = 10

EYEBROW_AR_THRESHOLD_MIN = 0.18
EYEBROW_AR_THRESHOLD_MAX = 0.25

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
ANCHOR_POINT = (0, 0)
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
(lbStart, lbEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"]
(rbStart, rbEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"]

# Video capture
vid = cv2.VideoCapture(0)
resolution_w = 1366
resolution_h = 768
cam_w = 640
cam_h = 480
unit_w = resolution_w / cam_w
unit_h = resolution_h / cam_h

INITIAL_ASPECT_RATIO = None

def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def distance(p1,p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p2[1] - p1[1]) ** 2)

while True:
    # Grab the frame from the threaded video file stream, resize
    # it, and convert it to grayscale
    # channels)
    _, frame = vid.read()
    frame = cv2.flip(frame, 1)
    frame = imutils.resize(frame, width=cam_w, height=cam_h)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the grayscale frame
    rects = detector(gray, 0)

    # Loop over the face detections
    if len(rects) > 0:
        rect = rects[0]
    else:
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        INITIAL_ASPECT_RATIO = None
        continue

    shape = predictor(gray, rect)
    shape = face_utils.shape_to_np(shape)

    rightEyeBrow = shape[rbStart:rbEnd]
    leftEyeBrow = shape[lbStart:lbEnd]
    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]


    leftEyeHull = cv2.convexHull(leftEye)
    rightEyeHull = cv2.convexHull(rightEye)
    cv2.drawContours(frame, [leftEyeHull], -1, YELLOW_COLOR, 1)
    cv2.drawContours(frame, [rightEyeHull], -1, YELLOW_COLOR, 1)

    x = [p[0][0] for p in leftEyeHull]
    y = [p[0][1] for p in leftEyeHull]
    centroid_left_eye = (sum(x) / len(leftEyeHull), sum(y) / len(leftEyeHull))

    x = [p[0][0] for p in rightEyeHull]
    y = [p[0][1] for p in rightEyeHull]
    centroid_right_eye = (sum(x) / len(rightEyeHull), sum(y) / len(rightEyeHull))

    centroid_left_eye = (int(centroid_left_eye[0]), int(centroid_left_eye[1]))
    centroid_right_eye = (int(centroid_right_eye[0]), int(centroid_right_eye[1]))



    # The frame was flipped
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

    # print(centroid_left_eyebrow,centroid_right_eyebrow,'\n\n\n\n\n\n\n')
    cv2.line(frame, centroid_left_eyebrow, centroid_right_eyebrow, YELLOW_COLOR, 1)
    cv2.line(frame, centroid_left_eyebrow, centroid_left_eye, YELLOW_COLOR, 1)
    cv2.line(frame, centroid_right_eyebrow, centroid_right_eye, YELLOW_COLOR, 1)
    cv2.line(frame, centroid_left_eye, centroid_right_eye, YELLOW_COLOR, 1)

    x_for_area = [centroid_left_eye[0], centroid_right_eye[0],
                  centroid_left_eyebrow[0], centroid_right_eyebrow[0]]
    y_for_area = [centroid_left_eye[1], centroid_right_eye[1],
                  centroid_left_eyebrow[1], centroid_right_eyebrow[1]]
    corners = [centroid_left_eye, centroid_right_eye,
                  centroid_left_eyebrow, centroid_right_eyebrow]

    # print(PolyArea(x_for_area, y_for_area))


    distance_left = distance(centroid_left_eye, centroid_left_eyebrow)
    distance_right = distance(centroid_right_eye, centroid_right_eyebrow)

    distance_top = distance(centroid_left_eyebrow, centroid_right_eyebrow)
    distance_bottom = distance(centroid_left_eye, centroid_right_eye)

    height = distance_left if distance_left > distance_right else distance_right
    width = distance_top if distance_top > distance_bottom else distance_bottom

    aspect_ratio = height/width
    if INITIAL_ASPECT_RATIO == None:
        INITIAL_ASPECT_RATIO = aspect_ratio

    if aspect_ratio<INITIAL_ASPECT_RATIO-0.05:
        print("Down")
    if aspect_ratio>INITIAL_ASPECT_RATIO+0.07:
        print("Up")



    cv2.drawContours(frame, [lefteyebrowhull], -1, YELLOW_COLOR, 1)
    cv2.drawContours(frame, [righteyebrowhull], -1, YELLOW_COLOR, 1)
    
    for (x, y) in np.concatenate((leftEyeBrow, rightEyeBrow), axis=0):
        cv2.circle(frame, (x, y), 2, GREEN_COLOR, -1)
        

    # Show the frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # If the `Esc` key was pressed, break from the loop
    if key == 27:
        break

# Do a bit of cleanup
cv2.destroyAllWindows()
vid.release()
