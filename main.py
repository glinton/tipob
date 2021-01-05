#!usr/bin/env python3
#coding=utf-8

import pyaudio
import sys
import time
import threading
import wave

from enum   import Enum
from random import randrange

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

def playAudio(f, stream, num):
    for x in range(0, num):
        data = f.readframes(chunk)

        while data:
            stream.write(data)
            data = f.readframes(chunk)

        f.rewind()


def playSound(filename, num):
    f = wave.open(filename, "rb")

    p = pyaudio.PyAudio()

    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),
                    channels = f.getnchannels(),
                    rate = f.getframerate(),
                    output = True)

    playAudio(f, stream, num)

    #stop stream
    stream.stop_stream()
    stream.close()

    #close PyAudio
    p.terminate()

def playBackgroundSound(filename, num):
    BackgroundAudio(playSound(filename, num)).start()
    # thread = BackgroundAudio(playSound(filename, num)).start()
    # thread.start()


# For playing audio without blocking the main thread
class BackgroundAudio(threading.Thread):

    def __init__(self, f):
        threading.Thread.__init__(self)
        self.daemon = True
        self.runner = f

    def run(self):
        self.runner()

def playBackground():
    filename1 = './audio/filler/Background-1.wav'
    playSound(filename1,99)
    # threading.Thread(target=playSound(filename1, 99), name="BackgroundMusic").start()

class Prompt(Enum):
    Twist = 0
    Pull = 1
    Bop = 2

def promptRandom():
    prompt = Prompt(randrange(3))

    playSound('./audio/prompt/'+prompt.name+'.wav', 1)
    # playBackgroundSound('./audio/prompt/'+prompt.name+'.wav', 1)
    # BackgroundAudio(playSound('./audio/prompt/'+prompt.name+'.wav', 1)).start()

    # todo: add timeout
    if getch() == prompt.name[0].lower():
        playSound('./audio/success/'+prompt.name+'.wav',1)
        # playBackgroundSound('./audio/success/'+prompt.name+'.wav',1)
        return True
    
    return False
    # else:
    #     # todo: randomize
    #     playSound('./audio/fail/TryAgain.wav',1)


# starting - press button (key) to begin
print("Press enter to begin")

# wait for user to start
input()

filename2 = './audio/filler/Background-2.wav'
filename3 = './audio/filler/Background-3.wav'
chunk = 1024

# initial seconds between prompts
interval = 2.0
# seconds to speed up
decrementor = 0.2
# number of wins before speeding up
winSpeed = 5

# start background music
BackgroundAudio(playBackground).start()

# playBackgroundSound(playSound(filename2, 99))

win = True
i = 0
while win:
    time.sleep(interval)
    win = promptRandom()
    i += 1
    if interval >= 0.2 and i % winSpeed == 0:
        interval-=decrementor

if win == False:
    playSound('./audio/fail/TryAgain.wav',1)

# background audio for diminishing x seconds 2seconds -.25 seconds
# random prompt actions
# success or fail - record to influx
