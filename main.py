#!/usr/bin/env python3
#coding=utf-8

import os
import pyaudio
import random
import signal
import sys
import time
import timeit
import threading
import wave

if False:
    import RPi.GPIO as gpio
    from influxdb_client import InfluxDBClient
else:
    gpio = lambda: True
    InfluxDBClient = lambda: True

from enum            import Enum
from multiprocessing import Process, Value

CHUNK    = 1024  # How much of the audio frame to read
GATHERED = False # Whether the prompted action has been completed
BOP      = 4     # GPIO pin locations of button
PULL     = 17    # GPIO pin locations of button
TWIST    = 27    # GPIO pin locations of button


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

# getGpioCH gets user input from rpi buttons
def getGpioCH():
    global GATHERED

    try:
        while True:
            if gpio.input(BOP):
                GATHERED = True
                return "b"
            elif gpio.input(PULL):
                GATHERED = True
                return "p"
            elif gpio.input(TWIST):
                GATHERED = True
                return "t"

    except:
        return "1"

def record(prompt, time):
    try:
        write_api.write("tipob", "my-org", ["tipob,reaction=" + promptName.lower() + " reaction_time=" + reaction_time])
    except:
        return True


def prompt(promptName):
    t = playBackgroundSound('./audio/prompt/'+promptName+'.wav', 1)
    start = time.time()

    global GATHERED
    GATHERED = False

    if getCH() == promptName[0].lower():
        t.join()

        # todo: thread
        record(promptName.lower(), str(time.time() - start))

        playSound('./audio/success/'+promptName+'.wav', 1, lambda: False)
        return True

    t.join()
    return False

# starting - press button (key) to begin
print("Press enter to begin")

# wait for user to start
input()

# initial seconds between prompts
interval = 1.5
# seconds to speed up
decrementor = 0.2
# number of wins before speeding up
winSpeed = 2

# rpi gpio button setup
try:
    gpio.setmode(gpio.BCM)
    gpio.setup(BOP, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(PULL, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(TWIST, gpio.IN, pull_up_down=gpio.PUD_DOWN)
except:
    print()
finally:
    try:
        gpio.cleanup()
    except:
        print()

# start background music
bgSwap = False
bgSound = threading.Thread(target=playSound, args=['./audio/filler/' + random.choice(os.listdir("./audio/filler/")), 99, lambda: bgSwap])
bgSound.start()

try:
    token = "$MYTOKEN"
    org = "my-org"
    client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    write_api = client.write_api()
except:
    write_api = lambda: True

win = True
wins = 0
while win:
    time.sleep(interval)

    # random prompt actions
    win = prompt(Prompt(random.randrange(3)).name)
    wins += 1

    if win:
        if wins % winSpeed == 0:
            if interval >= 0.2:
                interval-=decrementor

        # change background every 5 rounds
        if wins % 5 == 0:
            # start new sound
            bgSwap = True
            bgSound.join()
            bgSwap = False
            bgSound = threading.Thread(target=playSound, args=['./audio/filler/' + random.choice(os.listdir("./audio/filler/")), 99, lambda: bgSwap])
            bgSound.start()

if not win:
    # end background sound
    bgSwap = True
    bgSound.join()

    # play random failure sound
    rand_file = random.choice(os.listdir("./audio/fail"))
    playSound("./audio/fail/" + rand_file, 1, lambda: False)

print("You succeeded", wins-1, "times!")
# success or fail - record to influx
