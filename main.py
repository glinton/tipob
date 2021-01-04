#!usr/bin/env python  
#coding=utf-8  

import pyaudio  
import wave  
import sys
import time

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

    #read data  
        data = f.readframes(chunk)  

        #play stream  
        while data:  
            stream.write(data)  
            data = f.readframes(chunk)  

        f.rewind()


def playSound(filename, num):
    f = wave.open(filename,"rb")

    #instantiate PyAudio  
    p = pyaudio.PyAudio()  

    #open stream  
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                    channels = f.getnchannels(),  
                    rate = f.getframerate(),  
                    output = True)  

    # play 3 iterations of background audio
    playAudio(f, stream, num)

    #stop stream  
    stream.stop_stream()  
    stream.close()  

    #close PyAudio  
    p.terminate()

def promptBop():
    promptName = './audio/prompt/Bop It.wav'
    # todo: thread prompt, or thread getch and run first.
    playSound(promptName, 1)

    # todo: add timeout
    ch = getch()
    if ch != "b":
        # todo: randomize
        playSound('./audio/fail/TryAgain.wav',1)
    else:
        playSound('./audio/success/Bopped.wav',1)

def promptPull():
    promptName = './audio/prompt/Pull It.wav'
    playSound(promptName, 1)

    # todo: add timeout
    ch = getch()
    if ch != "p":
        # todo: randomize
        playSound('./audio/fail/TryAgain.wav',1)
    else:
        playSound('./audio/success/Pulled.wav',1)

def promptTwist():
    promptName = './audio/prompt/Twist It.wav'
    playSound(promptName, 1)

    # todo: add timeout
    ch = getch()
    if ch != "t":
        # todo: randomize
        playSound('./audio/fail/TryAgain.wav',1)
    else:
        playSound('./audio/success/Twisted.wav',1)

import threading


# for threading, this is a class
class BackgroundPlayer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

    def run(self):
        playBackground()

def playBackground():
    filename1 = './audio/filler/Background-1.wav'
    threading.Thread(target=playSound(filename1, 99), name="BackgroundMusic").start()


print("Press enter to begin")
# wait for user to start
input()

filename2 = './audio/filler/Background-2.wav'
filename3 = './audio/filler/Background-3.wav'
samplerate = 44100
chunk = 1024  

thread = BackgroundPlayer()
thread.start()
# playBackground()

# todo: fork this?
# playSound(filename1, 3)
time.sleep(2)
promptPull()

time.sleep(1.8)
promptBop()
# playSound(filename2, 2)

# playSound(filename3, 3)
time.sleep(1.6)
promptTwist()


# input()
# sys.stdin.read(1)


# starting - press button (key) to begin
# background audio for diminishing x seconds 2seconds -.25 seconds
# random prompt actions
# success or fail - record to influx

