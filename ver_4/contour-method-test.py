import cv2
import numpy as np
import dlib

cap = cv2.VideoCapture(0)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
eye = np.zeros((100, 100, 3), np.uint8)
thr = np.zeros((100, 100, 3), np.uint8)

def nothing(x):
    pass

cv2.namedWindow('frame')
cv2.createTrackbar('threshold', 'frame', 0, 255, nothing)

def midpoint(p1, p2):
    return int((p1.x + p2.x)/2), int((p1.y + p2.y))

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    threshold = cv2.getTrackbarPos('threshold', 'frame')
    if str(faces) == 'rectangles[]':
        pass
    else:
        for face in faces:
            x, y = face.left(), face.top()
            x1, y1 = face.right(), face.bottom()
            cv2.rectangle(frame, (x, y), (x1, y1), (0, 255, 0), 2)

            landmarks = predictor(gray, face)

            left_point = (landmarks.part(36).x, landmarks.part(36).y)
            right_point = (landmarks.part(39).x, landmarks.part(39).y)
            top_center = midpoint(landmarks.part(37), landmarks.part(38))
            bottom_center = midpoint(landmarks.part(41), landmarks.part(40))

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

            eye = frame[min_y-1: max_y, min_x : max_x]
            eye = cv2.resize(eye, None, fx=8, fy=8)
            gray_eye = cv2.cvtColor(eye, cv2.COLOR_BGR2GRAY)
            _, thr = cv2.threshold(gray_eye, threshold, 255, cv2.THRESH_BINARY_INV)
            edged = cv2.Canny(thr, threshold, 200)
            thr = cv2.GaussianBlur(thr, (3, 3), 0)
            thr = cv2.dilate(thr, None, iterations=3)
            thr = cv2.erode(thr, None, iterations=2)
            thr = cv2.medianBlur(thr, 5)
            x, y, h = eye.shape
            if x == y & x == 100:
                cont, h = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if len(cont) > 0:
                    print('detected')
                    cv2.drawContours(eye, cont, -1, (0, 0, 255), 3)
            cv2.polylines(frame, [left_eye_region], True, (0,0,255), 2)

    cv2.imshow('eye', eye)
    cv2.imshow('thr', thr)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xff == ord('q'):
        break
    

cap.release()
cv2.destroyAllWindows()