import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

import cv2
import mediapipe as mp
import pyautogui
import math
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialize webcam
cap = cv2.VideoCapture(0)  # Use your PC webcam

# Initialize MediaPipe Hands
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=2)
mpDraw = mp.solutions.drawing_utils

# Get screen resolution
screen_width, screen_height = pyautogui.size()

# Volume control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))

# Function to detect raised fingers
def fingers_up(lmList):
    tips = [8, 12, 16, 20]
    fingers = []
    for tip in tips:
        if lmList[tip][2] < lmList[tip - 2][2]:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers.count(1)

while True:
    success, img = cap.read()
    if not success or img is None:
        continue

    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)

    left_hand_fingers_up = 0
    right_hand_fingers_up = 0

    if results.multi_hand_landmarks:
        for i, handLms in enumerate(results.multi_hand_landmarks):
            lmList = []
            h, w, c = img.shape
            for id, lm in enumerate(handLms.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append((id, cx, cy))

            if lmList:
                # Move mouse with index finger
                x1, y1 = lmList[8][1], lmList[8][2]
                screen_x = int(screen_width / w * x1)
                screen_y = int(screen_height / h * y1)
                pyautogui.moveTo(screen_x, screen_y)

                # Detect click when thumb and index finger touch
                x2, y2 = lmList[4][1], lmList[4][2]
                distance = math.hypot(x2 - x1, y2 - y1)
                if distance < 30:
                    pyautogui.click()
                    cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)

                # Gesture-based actions
                fingers = fingers_up(lmList)
                if fingers == 1:
                    sbc.set_brightness(max(sbc.get_brightness()[0] - 10, 0))
                elif fingers == 2:
                    sbc.set_brightness(min(sbc.get_brightness()[0] + 10, 100))
                elif fingers == 3:
                    volume_ctrl.SetMasterVolumeLevelScalar(min(volume_ctrl.GetMasterVolumeLevelScalar() + 0.1, 1.0), None)
                elif fingers == 4:
                    volume_ctrl.SetMasterVolumeLevelScalar(max(volume_ctrl.GetMasterVolumeLevelScalar() - 0.1, 0.0), None)

                if i == 0:
                    left_hand_fingers_up = fingers
                elif i == 1:
                    right_hand_fingers_up = fingers

                # Minimize windows with both hands showing 2 fingers
                if left_hand_fingers_up == 2 and right_hand_fingers_up == 2:
                    pyautogui.hotkey('win', 'd')

            mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)

    cv2.imshow("Hand Gesture Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
