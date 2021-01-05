#!/usr/bin/env python3
#coding=utf-8

import pyaudio
import signal
import sys
import time
import threading
import wave
import timeit
from influxdb_client import InfluxDBClient

from enum            import Enum
from multiprocessing import Process, Value
from random          import randrange

CHUNK = 1024
GATHERED = False

def interrupted(signum, frame):
    if not GATHERED:
        raise Exception()

signal.signal(signal.SIGALRM, interrupted)

# Get single character from keyboard without pressing enter.
class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchUnix()
        except ImportError:
            self.impl = _GetchWindows()

    def __call__(self): return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

def playAudio(f, stream, num, stop):
    for x in range(0, num):
        data = f.readframes(CHUNK)

        while data:
            stream.write(data)
            data = f.readframes(CHUNK)

        f.rewind()

        if stop():
            break

def playSound(filename, num, stop):
    f = wave.open(filename, "rb")

    p = pyaudio.PyAudio()

    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                    channels = f.getnchannels(),
                    rate = f.getframerate(),
                    output = True)

    playAudio(f, stream, num, stop)

    stream.stop_stream()
    stream.close()

    p.terminate()

def playBackgroundSound(filename, num):
    t = threading.Thread(target=playSound, args=[filename, num, lambda: False])
    t.start()

    return t

class Prompt(Enum):
    Twist = 0
    Pull = 1
    Bop = 2

# getCH gets user input from the keyboard
def getCH():
    global GATHERED

    signal.alarm(2)
    try:
        ch = getch()
        GATHERED = True
        return ch
    except:
        return "1"

def prompt(promptName):
    t = playBackgroundSound('./audio/prompt/'+promptName+'.wav', 1)
    start = time.time()

    global GATHERED
    GATHERED = False

    if getCH() == promptName[0].lower():
        t.join()
        end = time.time() 
        reaction_time = str(end - start)
        write_api.write("tipob", "my-org", ["tipob,reaction=" + promptName[0].lower() + " reaction_time=" + reaction_time])

        playSound('./audio/success/'+promptName+'.wav', 1, lambda: False)
        return True

    t.join()
    return False

# starting - press button (key) to begin
print("Press enter to begin")

# wait for user to start
input()

# initial seconds between prompts
interval = 2.0
# seconds to speed up
decrementor = 0.2
# number of wins before speeding up
winSpeed = 5

# start background music
bgSwap = False
bgSound = threading.Thread(target=playSound, args=['./audio/filler/Background-'+str(randrange(13)+1)+'.wav', 99, lambda: bgSwap])
bgSound.start()

win = True
wins = 0
while win:
    time.sleep(interval)
    token = "$MYTOKEN"
    org = "my-org"
    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    write_api = client.write_api()

    # random prompt actions
    win = prompt(Prompt(randrange(3)).name)
    wins += 1

    if win == True and wins % winSpeed == 0:
        if interval >= 0.2:
            interval-=decrementor

        # start new sound
        bgSwap = True
        bgSound.join()
        bgSwap = False

        playSound('./audio/ShiftGear.wav', 1, lambda: False)

        bgSound = threading.Thread(target=playSound, args=['./audio/filler/Background-'+str(randrange(13)+1)+'.wav', 99, lambda: bgSwap])
        bgSound.start()

if win == False:
    # end background sound
    bgSwap = True
    bgSound.join()

    # todo: randomize failure
    playSound('./audio/fail/TryAgain.wav', 1, lambda: False)

print("You succeeded", wins-1, "times!")

# success or fail - record to influx
