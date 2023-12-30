import requests
import time

# This is the URL of the API endpoint
URL = "http://localhost:8080"

def getStatus(e):
    response = requests.get(URL + "/api/play/status")
    print(response.json())

def getIdlePlaying(e=None):
    response = requests.get(URL + "/api/play/status")
    stat = response.json()
    if stat == []:
        return False
    if stat != []:
        stat = stat[0]
        if stat["Sequence"]["Name"] == "idle":
            return True
    return False

def getSequencePlaying(e=None):
    response = requests.get(URL + "/api/play/status")
    stat = response.json()
    if stat == []:
        return False
    if stat != []:
        stat = stat[0]
        if stat["Sequence"]["Name"] != "idle":
            return True
    return False

def stopSequence(sequence):
    response = requests.post(URL + "/api/play/stopSequence", json=sequence)
    req = response.json()
    # print(f"stop req:{req}")
  
    if req["State"] != 0:
        return -1
    return 0

def stopCurrentSequence(e):
    # Get the status to find the currently playing sequence
    response = requests.get(URL + "/api/play/status")
    stat = response.json()
    if stat != []:
        stat = stat[0]
    
    if stat == []:
        print("No sequence is currently playing.")
        return 0
    else:
        print(f"Stopping the currently playing sequence: {stat['Sequence']['Name']}")
        return stopSequence(stat["Sequence"])

def stopIdle(e):
    # Get the status to find the currently playing sequence
    response = requests.get(URL + "/api/play/status")
    stat = response.json()
    if stat != []:
        stat = stat[0]
    
    if stat == []:
        print("No sequence is currently playing, idle need not be stopped.")
        return 0
    elif stat["Sequence"]["Name"] == "idle":
        print("Stopping idle")
        return stopSequence(stat["Sequence"])
    else:
        print("Idle is not currently playing.")
        return 0

def playSequence(sequence, force_play=False):

    # Get status:
    response = requests.get(URL + "/api/play/status")
    # print response contents
    stat = response.json()
    if stat != []:
        print(stat)
        stat = stat[0]
    # print(stat)


    if stat == []:
        # skip if no sequence is playing
        print("test1")
        pass
    elif int(stat['State']) == 1 and not force_play and not stat["Sequence"]["Name"] == "idle":
        print("Sequence already playing")
        return -1
    elif int(stat['State']) == 1 and not force_play and stat["Sequence"]["Name"] == "idle" and not sequence["Name"] == "idle":
        print("Idle already playing, stopping idle")
        # print("Then sleeping for 5")
        stopSequence(stat["Sequence"])
    elif int(stat['State']) == 1 and not force_play and stat["Sequence"]["Name"] == "idle" and sequence["Name"] == "idle":
        print("Idle already playing, and trying to play idle, skipping command")
        return -1
    elif force_play:
        print("Forcing play")
        sequence_playing = stat["Sequence"]
        if sequence_playing == sequence:
            return 0
        else:
            # print("Stopping, then sleeping for 5") 
            stopSequence(sequence_playing)
            time.sleep(5)

    # Play sequence:     
    req = requests.post(URL + "/api/play/playSequence", json=sequence)    
    # print(req)
