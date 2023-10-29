import cv2
import time
import os
from collections import deque
import numpy as np

temperature = 0
last_motion_time = 0
idle_time = 0

cap = cv2.VideoCapture(0)

centroid_list = deque(maxlen=20)  # A queue to keep the last 20 centroids
wave_detected = False

while True:
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    diff_frame = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff_frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) < 5000:
            continue

        motion_detected = True
        (x, y, w, h) = cv2.boundingRect(contour)
        centroid = (int(x + w / 2), int(y + h / 2))
        centroid_list.append(centroid)
        cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 3)

    if len(centroid_list) == 20:  # When we have 20 centroids
            x_values = np.array([pt[0] for pt in centroid_list])
            mean_x = np.mean(x_values)
            
            # Check for oscillations around the mean
            oscillate_count = 0
            for i in range(1, len(x_values)):
                if (x_values[i] > mean_x and x_values[i-1] < mean_x) or \
                (x_values[i] < mean_x and x_values[i-1] > mean_x):
                    oscillate_count += 1
                    
            if oscillate_count >= 4:  # If at least 4 oscillations occur, consider it as waving
                print("Wave detected")
                centroid_list.clear()  # Reset the centroid list

    if motion_detected and time.time() - last_motion_time >= 5:
        temperature += 1
        last_motion_time = time.time()

    cv2.imshow("Motion Detection", frame1)

    current_time = time.time()
    if current_time - last_motion_time >= 60:
        idle_time = max(idle_time, last_motion_time)
        if current_time - idle_time >= 5:
            temperature = max(0, temperature - 1)

    with open("temperature.txt", "w") as f:
        f.write(str(temperature))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
