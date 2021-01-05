#!/usr/bin/env python3
#coding=utf-8

import argparse
import os
import pyaudio
import random
import signal
import sys
import time
import timeit
import threading
import wave

from enum            import Enum
from multiprocessing import Process, Value

parser = argparse.ArgumentParser()
parser.add_argument("--pi", help="start on pi", action="store_true")
parser.add_argument("--influx", help="record stats to influx", action="store_true")
args = parser.parse_args()

if args.influx:
    from influxdb_client import InfluxDBClient
else:
    InfluxDBClient = lambda: True

if args.pi:
    import RPi.GPIO as gpio
else:
    gpio = lambda: True

###############################################
## GPIO pin/button configuration variables ####
BOP      = 4     # GPIO pin locations of button
PULL     = 17    # GPIO pin locations of button
TWIST    = 27    # GPIO pin locations of button
###############################################

#####################################
## Game configuration variables #####
# initial seconds between prompts
INTERVAL = 1.5
# seconds to speed up
DECREMENTOR = 0.2
# number of wins before speeding up
WIN_SPEED = 2
#####################################

###########################
## Non configurable vars ##
bgSwap    = False
bgSound   = None
write_api = None
gathered  = False # Whether the prompted action has been completed
chunk     = 1024  # How much of the audio frame to read
###########################

def interrupted(signum, frame):
    if not gathered:
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
        data = f.readframes(chunk)

        while data:
            stream.write(data)
            data = f.readframes(chunk)

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
    global gathered

    signal.alarm(2)
    try:
        ch = getch()
        gathered = True
        return ch
    except:
        return "1"

# getGpioCH gets user input from rpi buttons
def getGpioCH():
    global gathered

    try:
        while True:
            if gpio.input(BOP):
                gathered = True
                return "b"
            elif gpio.input(PULL):
                gathered = True
                return "p"
            elif gpio.input(TWIST):
                gathered = True
                return "t"

    except:
        return "1"

def record(prompt, time):
    if args.influx:
        try:
            write_api.write("tipob", "my-org", ["tipob,reaction=" + prompt + " reaction_time=" + time])
        except:
            print("Failed to write to influx")
    else:
        print("Executed", prompt, "in", time)

def prompt(promptName):
    t = playBackgroundSound('./audio/prompt/'+promptName+'.wav', 1)
    start = time.time()

    global gathered
    gathered = False

    ch = ""
    if args.pi:
        ch = getGpioCH()
    else:
        ch = getCH()

    if ch == promptName[0].lower():
        t.join()

        # todo: thread
        record(promptName.lower(), str(time.time() - start))

        playSound('./audio/success/'+promptName+'.wav', 1, lambda: False)
        return True

    t.join()
    return False

# rpi gpio button setup
def setupPi():
    gpio.setmode(gpio.BCM)
    gpio.setup(BOP, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(PULL, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    gpio.setup(TWIST, gpio.IN, pull_up_down=gpio.PUD_DOWN)


def startGame():
    # todo: play bop-it sound to prompt user to start game (pi version is headless)?

    # starting - press button (key) to begin
    print("Press enter to begin")

    # wait for user to start
    # todo: won't work on pi with buttons
    input()

# start background music
def startBackgroundMusic():
    global bgSwap, bgSound
    bgSwap = False
    bgSound = threading.Thread(target=playSound, args=['./audio/filler/' + random.choice(os.listdir("./audio/filler/")), 99, lambda: bgSwap])
    bgSound.start()

# end background music
def endBackgroundMusic():
    global bgSwap, bgSound
    bgSwap = True
    bgSound.join()

def setupInflux():
    global write_api
    try:
        token = "$MYTOKEN"
        org = "my-org"
        client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
        write_api = client.write_api()
    except:
        write_api = lambda: True

def startGameLoop():
    global INTERVAL, DECREMENTOR, WIN_SPEED

    win = True
    wins = 0
    while win:
        time.sleep(INTERVAL)

        # random prompt actions
        win = prompt(Prompt(random.randrange(3)).name)
        wins += 1

        if win:
            if wins % WIN_SPEED == 0:
                if INTERVAL >= 0.2:
                    INTERVAL-=DECREMENTOR

            # change background every 5 rounds
            if wins % 5 == 0:
                endBackgroundMusic()
                startBackgroundMusic()

    if not win:
        endBackgroundMusic()

        # play random failure sound
        rand_file = random.choice(os.listdir("./audio/fail"))
        playSound("./audio/fail/" + rand_file, 1, lambda: False)

    print("You succeeded", wins-1, "times!")

def main():
    # Setup gpio/pi buttons
    if args.pi:
        try:
            setupPi()
        except:
            True
        finally:
            gpio.cleanup()
    
    if args.influx:
        setupInflux()

    # Prompt for start
    startGame()

    startBackgroundMusic()

    startGameLoop()

if __name__ == "__main__":
    main()
