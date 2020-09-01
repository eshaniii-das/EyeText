from PyQt5 import QtWidgets, QtGui, QtCore, uic
from PyQt5.QtWidgets import QWidget, QMainWindow, QHBoxLayout, QGridLayout, QApplication, QLabel, QVBoxLayout, QBoxLayout, QPushButton, QSlider, QMessageBox
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QObject, QThread
import sys
import cv2
import numpy as np
import os
import pyautogui
import dlib
import threading

os.chdir('/home/aryan/Documents/Python/EyeText/ver_3')
eyeCoordinatesAtCenter = (0, 0)

screenX, screenY = pyautogui.size()

class videoThread(QThread):
    global screenX, screenY
    change_frame_pixmap_signal=pyqtSignal(np.ndarray)
    change_eye_pixmap_signal=pyqtSignal(np.ndarray)
    callibrationScreen = np.zeros((screenY, screenX, 3), np.uint8)
    threshold = 0
    zoom = 1
    coordinates = (0, 0)
    callibrationStatus = False
    listOfCoords = []
    indexCoords = 0

    def midpoint(self, p1 ,p2):
        return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)

    def on_threshold(self, x):
        pass


    def testTracking(self):
        ratioX = int(960/eyeCoordinatesAtCenter[0])
        ratioY = int(540/eyeCoordinatesAtCenter[1])
        xdiff = eyeCoordinatesAtCenter[0] - self.listOfCoords[self.indexCoords][0]
        ydiff = eyeCoordinatesAtCenter[1] - self.listOfCoords[self.indexCoords][1]

        if self.coordinates[0] >= eyeCoordinatesAtCenter[0]:
            if self.coordinates[1] >= eyeCoordinatesAtCenter[1]:
                gazePosition = ((int(screenX/2))+(xdiff*ratioX), (int(screenY/2))-(ydiff*ratioY))
            if self.coordinates[1] <= eyeCoordinatesAtCenter[1]: 
                gazePosition = ((int(screenX/2))+(xdiff*ratioX), (int(screenY/2))+(ydiff*ratioY))

        if self.coordinates[0] <= eyeCoordinatesAtCenter[0]:
            if self.coordinates[1] >= eyeCoordinatesAtCenter[1]:
                gazePosition = ((int(screenX/2))-(xdiff*ratioX), (int(screenY/2))-(ydiff*ratioY*10))
            if self.coordinates[1] <= eyeCoordinatesAtCenter[1]:
                gazePosition = ((int(screenX/2))-(xdiff*ratioX), (int(screenY/2))+(ydiff*ratioY*10))
        # gazePosition = (self.coordinates[0]*ratioY, self.coordinates[1]*ratioX)
        cv2.circle(self.callibrationScreen, gazePosition, 3, (0, 0, 255), -1)

    def click_pos(self, event, x, y, flags, params):
        global click
        if event == cv2.EVENT_LBUTTONDOWN:
            click = True
        else:
            click = False

    def blob_process(self, img, detection):
        img = cv2.erode(img, None, iterations=2)
        img = cv2.dilate(img, None, iterations=30)
        img = cv2.medianBlur(img, 5)
        keypoints = detection.detect(img)
        return keypoints

    def run(self):
        cap = cv2.VideoCapture(0)
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

        eyeFrame = np.zeros((150, 300, 3), np.uint8)
        eyeFrame[:] = 40

        detector_params = cv2.SimpleBlobDetector_Params()
        detector_params.filterByColor = True
        detector_params.blobColor = 255
        #detector_params.filterByArea = True
        #detector_params.maxArea = 3000
        blob_detector = cv2.SimpleBlobDetector_create(detector_params)
        global eyeCoordinatesAtCenter

        while True:
            ret, img = cap.read()
            # img = cv2.flip(img, 1)
            img = cv2.resize(img, None, fx=0.5, fy=0.5)
            grayImg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector(grayImg)
            if len(faces) != 0:
                for face in faces:
                    facex, facey = face.left(), face.top()
                    facex1, facey1 = face.right(), face.bottom()

                    # draws a rectangle around the face
                    cv2.rectangle(img, (facex, facey), (facex1, facey1),
                        (0, 0, 255), thickness=2)
                    landmarks = predictor(grayImg, face)

                    left_point = (landmarks.part(36).x, landmarks.part(36).y)
                    right_point = (landmarks.part(39).x, landmarks.part(39).y)
                    top_center = self.midpoint(landmarks.part(37), landmarks.part(38))
                    bottom_center = self.midpoint(landmarks.part(41), landmarks.part(40))
                    
                    #Gaze Ratio
                    left_eye_region = np.array([(landmarks.part(36).x, landmarks.part(36).y),
                                (landmarks.part(37).x, landmarks.part(37).y),
                                (landmarks.part(38).x, landmarks.part(38).y),
                                (landmarks.part(39).x, landmarks.part(39).y),
                                (landmarks.part(40).x, landmarks.part(40).y),
                                (landmarks.part(41).x, landmarks.part(41).y)], np.int32)

                    min_x = np.min(left_eye_region[:, 0])
                    max_x = np.max(left_eye_region[:, 0])
                    min_y = np.min(left_eye_region[:, 1])
                    max_y = np.max(left_eye_region[:, 1])

                    eye = img[min_y-1: max_y, min_x : max_x]
                    eye = cv2.resize(eye, None, fx=self.zoom, fy=self.zoom)
                    
                    gray_eye = cv2.cvtColor(eye, cv2.COLOR_BGR2GRAY)
                    threshold = cv2.getTrackbarPos('threshold', 'eyeWindow')
                    _, eyeImg = cv2.threshold(gray_eye, self.threshold, 255, cv2.THRESH_BINARY_INV)
                    keypoints = self.blob_process(eyeImg, blob_detector)
                    # print(keypoints)
                    for keypoint in keypoints:
                        s = keypoint.size
                        x = keypoint.pt[0]
                        y = keypoint.pt[1]
                        cx = int(x)
                        cy = int(y)
                        self.coordinates = (cx, cy)
                        cv2.circle(eye, (cx, cy), 5, (0, 0, 255), -1)
                        self.listOfCoords.append(self.coordinates)
                    
                    cv2.drawKeypoints(eye, keypoints, eye, (0, 255, 0), 
                            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

                    cv2.polylines(img, [left_eye_region], True, (255, 0, 255), 2)
                    ey, ex, ch = eye.shape
                    eyeFrame[int(75-(ey/2)):int(75+(ey/2)), int(150-(ex/2)):int(150+(ex/2))] = eye
                    # print(eyeCoordinatesAtCenter, self.coordinates)
                    if self.callibrationStatus == True:
                        self.testTracking()
                        cv2.imshow('screen', self.callibrationScreen)

            if ret:
                self.change_frame_pixmap_signal.emit(img)
                self.change_eye_pixmap_signal.emit(eyeFrame)


class App(QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        global screenX, screenY
        if (screenX, screenY) == (1920, 1080):
            uic.loadUi('eyeWriterInterface-largeMonitor.ui', self)
        else:
            uic.loadUi('eyeWriterInterface-smallMonitor.ui', self)

        self.setGeometry(0, 0, screenX, screenY)
        self.xIcon = self.findChild(QtWidgets.QLabel, 'xIcon')
        self.xIcon.hide()
        self.testTracking = self.findChild(QtWidgets.QWidget, 'testTracking')
        self.testTracking.hide()

        self.frame_label = self.findChild(QtWidgets.QLabel, 'frame_label')
        self.eye_label = self.findChild(QtWidgets.QLabel, 'eye_label')

        self.thresholdSlider = self.findChild(QtWidgets.QSlider, 'thresholdSlider')
        self.thresholdSlider.valueChanged[int].connect(self.thresholdChanged)

        self.zoomSlider = self.findChild(QtWidgets.QSlider, 'zoomSlider')
        self.zoomSlider.valueChanged[int].connect(self.zoomChanged)

        self.startVideo = self.findChild(QtWidgets.QPushButton, 'startVideo')
        self.startVideo.clicked.connect(self.startVideoClicked)

        self.clickCenter = self.findChild(QtWidgets.QPushButton, 'clickCenter')
        self.clickCenter.clicked.connect(self.ifCenterClicked)
        self.clickCenter.hide()

        self.callibrate = self.findChild(QtWidgets.QPushButton, 'callibrate')
        self.callibrate.clicked.connect(self.callibrateClicked)
        self.show()

    @pyqtSlot(np.ndarray)
    def updateFrameImage(self, img):
        self.qtImg = self.convertCvQt(img)
        self.frame_label.setPixmap(self.qtImg)

    @pyqtSlot(np.ndarray)
    def updateEyeImage(self, img):
        self.eyeImg = self.convertCvQt(img)
        self.eye_label.setPixmap(self.eyeImg)

    def convertCvQt(self, img):
        rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImg.shape
        bytesPerLine = ch * w
        convertToQtFormat = QtGui.QImage(rgbImg.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
        #p = convertToQtFormat.scaled(self.width, self.height, Qt.KeepAspectRatio)
        p = convertToQtFormat
        return QPixmap.fromImage(p)

    def startVideoClicked(self):
        self.thread = videoThread()
        self.thread.change_frame_pixmap_signal.connect(self.updateFrameImage)
        self.thread.change_eye_pixmap_signal.connect(self.updateEyeImage)
        self.thread.start()

    def thresholdChanged(self, value):
        self.thread.threshold = value

    def zoomChanged(self, value):
        self.thread.zoom = value

    def callibrateClicked(self):
        self.xIcon.show()
        self.clickCenter.show()
        self.callibrationInstructions = QMessageBox.about(self, 'Instructions', 'Look at the X on the screen and click the CENTER button')

    def ifCenterClicked(self):
        global eyeCoordinatesAtCenter
        if self.thread.coordinates != (0, 0):
            eyeCoordinatesAtCenter = self.thread.coordinates
        else:
            QMessageBox.about(self, 'Try Again')
        # print(eyeCoordinatesAtCenter)
        self.thread.callibrationStatus = True
        self.xIcon.hide()
        self.clickCenter.hide()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())