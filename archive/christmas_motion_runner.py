import cv2
import time
import os

temperature = 0
last_motion_time = 0  # To keep track of the last time motion was detected
idle_time = 0  # To track idle time (no movement)

cap = cv2.VideoCapture(0)  # Use 0 for default camera
print(os.getcwd())
while True:
    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Compute the absolute difference between two frames
    diff_frame = cv2.absdiff(frame1, frame2)

    # Convert to grayscale and apply blur
    gray = cv2.cvtColor(diff_frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect motion
    _, thresh = cv2.threshold(blur, 10, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    motion_detected = False
    for contour in contours:
        if cv2.contourArea(contour) < 5000:
            continue
        motion_detected = True
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 3)

    if motion_detected and time.time() - last_motion_time >= 5:
        temperature += 1
        temperature = min(100, temperature)
        last_motion_time = time.time()

    # Show frame
    cv2.imshow("Motion Detection", frame1)

    # Check for idle time
    current_time = time.time()
    if current_time - last_motion_time >= 60:  # 5 minutes
        if idle_time == 0:
            idle_time = current_time
        if current_time - idle_time >= 10:
            temperature = max(0, temperature - 1)
            idle_time = current_time  # Reset idle time

    if current_time - last_motion_time >= 1800:  # 30 minutes
        temperature = 0

    with open("temperature.txt", "w") as f:
        f.write(str(temperature))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
