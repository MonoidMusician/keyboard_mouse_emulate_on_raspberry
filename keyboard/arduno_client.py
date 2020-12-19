#!/usr/bin/python
#
# YAPTB Bluetooth keyboard emulation service
# keyboard copy client.
# Reads local key events and forwards them to the btk_server DBUS service
#
# Adapted from www.linuxuser.co.uk/tutorials/emulate-a-bluetooth-keyboard-with-the-raspberry-pi
#
#
import os #used to all external commands
import sys # used to exit the script
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import serial
import evdev # used to get input from the keyboard
from evdev import *
import keymap # used to map evdev input to hid keodes



#Define a client to listen to local key events
class Keyboard():

    def __init__(self):
        #the structure for a bt keyboard input report (size is 10 bytes)

        self.state=[
            0xA1, #this is an input report
            0x01, #Usage report = Keyboard
            #Bit array for Modifier keys
            [0,    #Right GUI - Windows Key
             0,    #Right ALT
             0,    #Right Shift
             0,    #Right Control
             0,    #Left GUI
             0,    #Left ALT
             0,    #Left Shift
             0],   #Left Control
            0x00,  #Vendor reserved
            0x00,  #rest is space for 6 keys
            0x00,
            0x00,
            0x00,
            0x00,
            0x00]

        print "setting up DBus Client"

        self.bus = dbus.SystemBus()
        self.btkservice = self.bus.get_object('org.yaptb.btkbservice','/org/yaptb/btkbservice')
        self.iface = dbus.Interface(self.btkservice,'org.yaptb.btkbservice')

        print "waiting for keyboard"

        #keep trying to key a keyboard
        have_dev = False
        while have_dev == False:
            try:
                #try and get a keyboard - should always be event0 as
                #we're only plugging one thing in
                #self.dev = serial.Serial('/dev/ttyACM0', 9600)
                self.dev = serial.Serial('/dev/rfcomm0', 9600)
                have_dev=True
            except OSError:
                print "Keyboard not found, waiting 3 seconds and retrying"
                time.sleep(3)
            print "found a keyboard"

    def change_state(self,event):
        self.state[4] = ord(event[2])

    #poll for keyboard events
    def event_loop(self):
        while True:
            event = self.dev.read(8)
            self.change_state(event)
            self.send_input()

    #forward keyboard events to the dbus service
    def send_input(self):
        bin_str=""
        element=self.state[2]
        for bit in element:
            bin_str += str(bit)

        #print(self.state)
        self.iface.send_keys(int(bin_str,2),self.state[4:10])

if __name__ == "__main__":

    print "Setting up keyboard"

    kb = Keyboard()

    print "starting event loop"
    kb.event_loop()
