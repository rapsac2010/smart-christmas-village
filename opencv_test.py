import cv2

i = 0
def motion_detected():
    global i
    i += 1
    print(f"Motion detected!: {i}")

# Initialize the average frame (background)
avg = None

# Capture video from the first camera device
video = cv2.VideoCapture(0)

while True:
    motion_flag = False
    
    # Capture the frame
    check, frame = video.read()
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    # Initialize the average frame if it's None
    if avg is None:
        avg = gray.copy().astype("float")
        continue

    # Accumulate the weighted average between the current frame and previous frames
    cv2.accumulateWeighted(gray, avg, 0.5)  # Adjust the weight (0.5 here) to determine how quickly the average adapts
    frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
    
    # Thresholding the delta image
    thresh = cv2.threshold(frame_delta, 30, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    
    # Finding contours
    (contours, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        if cv2.contourArea(contour) < 1000:  # Adjust this value as per your sensitivity preference
            continue
        motion_flag = True
        break

    if motion_flag:
        motion_detected()

    # Delay to reduce CPU usage
    cv2.waitKey(1000)  # 100ms delay

video.release()
