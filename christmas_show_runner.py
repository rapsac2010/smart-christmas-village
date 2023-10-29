import requests
import json
import time
import random
import keyboard
import threading
import vixen_commands as vc
import fasteners

last_2_songs = []
temperature_lock = threading.Lock()
gesture_lock = threading.Lock()
temperature = 0
last_gesture = None
last_gesture_time = 0
last_performed_gesture_time = time.time()

def read_temperature():
    global temperature, last_gesture, last_gesture_time, last_performed_gesture_time
    lock = fasteners.InterProcessLock('data.json.lock')

    while True:
        s = 3
        got_lock = False
        try:
            got_lock = lock.acquire(blocking=True, timeout=10)  # timeout in seconds
            if got_lock:
                with open("data.json", "r") as f:
                    data = json.load(f)
                    with temperature_lock:
                        temperature = data['temperature']
                    with gesture_lock:
                        last_gesture = data['gesture']
                        last_gesture_time = data['last_gesture_time']
        finally:
            if got_lock:
                lock.release()

        # Your existing logic
        if temperature > 0:
            # Get 1 with p=temperature/100
            print(f"Idle playing {vc.getIdlePlaying(None)}")
            if random.choices([0, 1], weights=[1-temperature/(100*(60/s)), temperature/(30*(100/s))])[0] == 1:
                print("Playing random song")
                vc.stopIdle(None)
                time.sleep(4)
                play_random_song(None)
            elif not vc.getIdlePlaying(None):
                play_idle(None)
        
        if last_gesture_time > last_performed_gesture_time + 5:
            print("Gesture detected")
            print(last_gesture)
            if last_gesture == "Thumb_Down":
                last_performed_gesture_time = time.time()
                vc.stopIdle(None)
                time.sleep(4)
                force_random_song  (None)
                time.sleep(4)


        print(f"Temperature: {temperature}")
        time.sleep(s)  # Sleep for 60 seconds before reading again

# Sequences:
idle = [
    {"Name": "idle", "FileName": "idle.tim"}
]

# Songs: Sugar Plum Fairy, Jingle bell rock, Blue Christmas, Wizards in Winter (wiw), lonely this christmas, all I want 
songs = [
    {"Name": "Sugar Plum Fairy", "FileName": "sugar_plum_fairy.tim"},
    {"Name": "Blue Christmas", "FileName": "blue_christmas.tim"},
    {"Name": "Jingle bell rock", "FileName": "jingle_bell_rock.tim"},
    {"Name": "Lonely this Christmas", "FileName": "lonely_this_christmas.tim"},
    {"Name": "Wizards in Winter", "FileName": "wiw.tim"},
    {"Name": "All I want for Christmas", "FileName": "all_i_want.tim"}
]

def play_random_song(e):
    print(e)

    if vc.getSequencePlaying():
        print('sequence already playing, skipping command')
        return -1
    
    song = random.choice(songs)
    while song in last_2_songs:
        song = random.choice(songs)


    last_2_songs.append(song)
    if len(last_2_songs) > 2:
        last_2_songs.pop(0)
    
    vc.playSequence(song, False)

def force_random_song(e):
    song = random.choice(songs)
    while song in last_2_songs:
        song = random.choice(songs)
    last_2_songs.append(song)
    if len(last_2_songs) > 2:
        last_2_songs.pop(0)

    vc.playSequence(song, True)

def play_idle(e):
    vc.playSequence(idle[0], False)

temperature_thread = threading.Thread(target=read_temperature)
temperature_thread.start()

# When space is pressed play a random song, when enter is pressed play idle
keyboard.on_press_key("space", play_random_song)
keyboard.on_press_key("enter", play_idle)
keyboard.on_press_key('i', vc.getStatus)
keyboard.on_press_key('s', vc.stopCurrentSequence)
keyboard.on_press_key('f', force_random_song)
keyboard.wait('esc')

