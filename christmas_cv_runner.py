# Copyright 2023 The MediaPipe Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main scripts to run gesture recognition."""

import argparse
import sys
import time
import json
from collections import Counter, deque

import cv2
import mediapipe as mp
import fasteners

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

temperature = 0
last_temperature = 0
last_motion_time = 0  # To keep track of the last time motion was detected
idle_time = 0  # To track idle time (no movement)
last_gesture_time = 0
last_gesture = None
gesture_queue = deque(maxlen=10)  # Stores the last 5 gestures
min_gesture_count = 8  # Minimum number of the same gesture needed to confirm it
last_write_time = 0

# Global variables to calculate FPS
COUNTER, FPS = 0, 0
START_TIME = time.time()

def interpret_gesture_and_motion(gesture, motion_detected):
    global temperature, last_motion_time, idle_time, last_gesture_time, last_gesture, last_write_time, last_temperature
    cur_time = time.time()

    if idle_time == 0:
        idle_time = cur_time
    if last_gesture_time == 0:
        last_gesture_time = cur_time

    # 5 is temp increase delay
    if motion_detected and cur_time - last_motion_time >= 5:
        last_temperature = temperature
        temperature += 1
        temperature = min(100, temperature)
        last_motion_time = cur_time
    
    # 60 is cooldown period before temp starts to decrease
    if cur_time - last_motion_time >= 60:
        if cur_time - idle_time >= 10:
            last_temperature = temperature
            temperature = max(0, temperature - 1)
            idle_time = cur_time
        if cur_time - last_motion_time >= 1800:
           last_temperature = temperature
           temperature = 0
    
    if gesture is not None and gesture != 'None' and cur_time - last_gesture_time >= 0.2:
        gesture_queue.append(gesture)
        gesture_count = Counter(gesture_queue)
        common_gesture, count = gesture_count.most_common(1)[0]

        if count >= min_gesture_count and common_gesture != 'None':
            last_gesture = common_gesture
            last_gesture_time = cur_time
    elif (gesture == 'None' or gesture is None) and cur_time - last_gesture_time >= 0.2:
        gesture_queue.append('None')

    data = {'temperature': temperature, 'gesture': last_gesture, 'last_gesture_time': last_gesture_time}

    lock = fasteners.InterProcessLock('data.json.lock')
    got_lock = False
    try:
        # Try to acquire the lock, but don't block.
        got_lock = lock.acquire(blocking=False)
        if got_lock:
            with open('data.json', 'w') as f:
                json.dump(data, f)
    finally:
        # If lock was acquired, release it.
        if got_lock:
            lock.release()
   

def detect_motion(frame1, frame2):
    diff_frame = cv2.absdiff(frame1, frame2)
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
    
    return motion_detected, frame1
    


def run(model: str, num_hands: int,
        min_hand_detection_confidence: float,
        min_hand_presence_confidence: float, min_tracking_confidence: float,
        camera_id: int, width: int, height: int) -> None:
  """Continuously run inference on images acquired from the camera.

  Args:
      model: Name of the gesture recognition model bundle.
      num_hands: Max number of hands can be detected by the recognizer.
      min_hand_detection_confidence: The minimum confidence score for hand
        detection to be considered successful.
      min_hand_presence_confidence: The minimum confidence score of hand
        presence score in the hand landmark detection.
      min_tracking_confidence: The minimum confidence score for the hand
        tracking to be considered successful.
      camera_id: The camera id to be passed to OpenCV.
      width: The width of the frame captured from the camera.
      height: The height of the frame captured from the camera.
  """

  # Start capturing video input from the camera
  cap = cv2.VideoCapture(camera_id)
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

  # Visualization parameters
  row_size = 50  # pixels
  left_margin = 24  # pixels
  text_color = (0, 0, 0)  # black
  font_size = 1
  font_thickness = 1
  fps_avg_frame_count = 10

  # Label box parameters
  label_text_color = (0, 0, 0)  # red
  label_background_color = (255, 255, 255)  # white
  label_font_size = 1
  label_thickness = 2
  label_padding_width = 100  # pixels

  recognition_frame = None
  recognition_result_list = []

  def save_result(result: vision.GestureRecognizerResult,
                  unused_output_image: mp.Image, timestamp_ms: int):
      global FPS, COUNTER, START_TIME

      # Calculate the FPS
      if COUNTER % fps_avg_frame_count == 0:
          FPS = fps_avg_frame_count / (time.time() - START_TIME)
          START_TIME = time.time()

      recognition_result_list.append(result)
      COUNTER += 1

  # Initialize the gesture recognizer model
  base_options = python.BaseOptions(model_asset_path=model)
  options = vision.GestureRecognizerOptions(base_options=base_options,
                                          running_mode=vision.RunningMode.LIVE_STREAM,
                                          num_hands=num_hands,
                                          min_hand_detection_confidence=min_hand_detection_confidence,
                                          min_hand_presence_confidence=min_hand_presence_confidence,
                                          min_tracking_confidence=min_tracking_confidence,
                                          result_callback=save_result)
  recognizer = vision.GestureRecognizer.create_from_options(options)

  # Continuously capture images from the camera and run inference
  while cap.isOpened():
    success, image = cap.read()
    success2, image2 = cap.read()
    if not success or not success2:
      sys.exit(
          'ERROR: Unable to read from webcam. Please verify your webcam settings.'
      )
    
    motion_detected, image = detect_motion(image, image2)
    image = cv2.flip(image, 1)

    # Convert the image from BGR to RGB as required by the TFLite model.
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    # Run gesture recognizer using the model.
    recognizer.recognize_async(mp_image, time.time_ns() // 1_000_000)

    # Show the FPS
    fps_text = 'FPS = {:.1f}'.format(FPS)
    text_location = (left_margin, row_size)
    current_frame = image
    cv2.putText(current_frame, fps_text, text_location, cv2.FONT_HERSHEY_DUPLEX,
                font_size, text_color, font_thickness, cv2.LINE_AA)

    # Draw the hand landmarks.
    if recognition_result_list:
        # Draw landmarks.
        for hand_landmarks in recognition_result_list[0].hand_landmarks:
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
                landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y,
                                                z=landmark.z) for landmark in
                hand_landmarks
            ])
            mp_drawing.draw_landmarks(
                current_frame,
                hand_landmarks_proto,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

    # Expand the frame to show the labels.
    current_frame = cv2.copyMakeBorder(current_frame, 0, label_padding_width,
                                       0, 0,
                                       cv2.BORDER_CONSTANT, None,
                                       label_background_color)

    gesture = None
    if recognition_result_list:
      # Show top gesture classification.
      gestures = recognition_result_list[0].gestures

      if gestures:
        category_name = gestures[0][0].category_name
        if category_name != 'None':
            gesture = category_name
        score = round(gestures[0][0].score, 2)
        result_text = category_name + ' (' + str(score) + ')'

        # Compute text size
        text_size = \
        cv2.getTextSize(result_text, cv2.FONT_HERSHEY_DUPLEX, label_font_size,
                        label_thickness)[0]
        text_width, text_height = text_size

        # Compute centered x, y coordinates
        legend_x = (current_frame.shape[1] - text_width) // 2
        legend_y = current_frame.shape[0] - (
                    label_padding_width - text_height) // 2

        # Draw the text
        cv2.putText(current_frame, result_text, (legend_x, legend_y),
                    cv2.FONT_HERSHEY_DUPLEX, label_font_size,
                    label_text_color, label_thickness, cv2.LINE_AA)

      recognition_frame = current_frame
      recognition_result_list.clear()

    interpret_gesture_and_motion(gesture, motion_detected)

    if recognition_frame is not None:
        cv2.imshow('gesture_recognition', recognition_frame)

    # Stop the program if the ESC key is pressed.
    if cv2.waitKey(1) == 27:
        break

  recognizer.close()
  cap.release()
  cv2.destroyAllWindows()


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model',
      help='Name of gesture recognition model.',
      required=False,
      default='gesture_recognizer.task')
  parser.add_argument(
      '--numHands',
      help='Max number of hands that can be detected by the recognizer.',
      required=False,
      default=1)
  parser.add_argument(
      '--minHandDetectionConfidence',
      help='The minimum confidence score for hand detection to be considered '
           'successful.',
      required=False,
      default=0.5)
  parser.add_argument(
      '--minHandPresenceConfidence',
      help='The minimum confidence score of hand presence score in the hand '
           'landmark detection.',
      required=False,
      default=0.5)
  parser.add_argument(
      '--minTrackingConfidence',
      help='The minimum confidence score for the hand tracking to be '
           'considered successful.',
      required=False,
      default=0.5)
  # Finding the camera ID can be very reliant on platform-dependent methods. 
  # One common approach is to use the fact that camera IDs are usually indexed sequentially by the OS, starting from 0. 
  # Here, we use OpenCV and create a VideoCapture object for each potential ID with 'cap = cv2.VideoCapture(i)'.
  # If 'cap' is None or not 'cap.isOpened()', it indicates the camera ID is not available.
  parser.add_argument(
      '--cameraId', help='Id of camera.', required=False, default=0)
  parser.add_argument(
      '--frameWidth',
      help='Width of frame to capture from camera.',
      required=False,
      default=640)
  parser.add_argument(
      '--frameHeight',
      help='Height of frame to capture from camera.',
      required=False,
      default=480)
  args = parser.parse_args()

  run(args.model, int(args.numHands), args.minHandDetectionConfidence,
      args.minHandPresenceConfidence, args.minTrackingConfidence,
      int(args.cameraId), args.frameWidth, args.frameHeight)


if __name__ == '__main__':
  main()