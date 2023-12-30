import requests
import json
import time
import random
import keyboard
import threading
import vixen_commands as vc
import datetime  # Importing datetime for time checks

last_2_songs = []
temperature_lock = threading.Lock()
gesture_lock = threading.Lock()
temperature = 0
last_gesture = None
last_gesture_time = 0
last_performed_gesture_time = time.time()

# Function to check if current time is within a specified interval
def is_time_in_interval(start_time, end_time):
    current_time = datetime.datetime.now().time()
    return start_time <= current_time <= end_time

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

# Schedule times
idle_start_time = datetime.time(9, 0)  # Start time for idle animation (9:00)
idle_end_time = datetime.time(23, 0)  # End time for idle animation (23:00)
song_start_time = datetime.time(9, 10)  # Start time for playing songs (10:00)
song_end_time = datetime.time(22, 50)  # End time for playing songs (20:00)
avg_plays_per_hour = 3  # Average number of times a song is played per hour


# When space is pressed play a random song, when enter is pressed play idle
keyboard.on_press_key("space", play_random_song)

while True:
    print("Script started")
    # Check if current time is within the idle animation schedule
    if is_time_in_interval(idle_start_time, idle_end_time):
        print("time in interval 1")
        # Check if current time is within the song playing schedule
        if is_time_in_interval(song_start_time, song_end_time):
            print("time in interval 2")
            # Play random song based on avg_plays_per_hour
            if random.choices([True, False], weights=[avg_plays_per_hour/36000, 1 - avg_plays_per_hour/36000])[0]:
                print("Playing random song")
                play_random_song(None)
            else:
                # Outside song schedule but within idle schedule, play idle animation
                print("Playing idle")
                play_idle(None)
    time.sleep(10)  # Sleep for 60 seconds before checking again
