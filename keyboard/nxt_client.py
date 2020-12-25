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
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import time
import nxt
import nxt.bluesock
import evdev # used to get input from the keyboard
from evdev import *
import keymap # used to map evdev input to hid keodes
import _thread
import subprocess

sleep = time.sleep

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

        print("setting up DBus Client")

        self.bus = dbus.SystemBus()
        self.bus.watch_name_owner('org.yaptb.btkbservice', self.handle_btkservice)
        self.btkservice = None
        self.iface = None

        self.dev = None

        self.message_offset = 0
        self.messages = ["","","","","","","",""]
        self.messages = self.messages[0:3]

        print("waiting for keyboard")

        #keep trying to key a keyboard
        have_dev = False
        while have_dev == False:
            try:
                self.dev = nxt.bluesock.BlueSock('00:16:53:0A:FB:79').connect()
                self.dev.b0 = nxt.Touch(self.dev, 3)
                self.dev.b1 = nxt.Touch(self.dev, 0)
                self.l = False
                self.r = False
                have_dev=True
                print("found a keyboard")
            except OSError as e:
                print(e)
                print("Keyboard not found, waiting 5 seconds and retrying")
                time.sleep(5)

    def handle_btkservice(self, name):
        if name:
            self.btkservice = self.bus.get_object('org.yaptb.btkbservice','/org/yaptb/btkbservice')
            self.iface = dbus.Interface(self.btkservice,'org.yaptb.btkbservice')
            self.connected = self.iface.is_connected()
            self.on_connect()
            self.iface.connect_to_signal('connection_changed', self.on_connect)
        else:
            self.btkservice = self.iface = None
            self.connected = None
            self.on_connect()

    def change_state(self,event):
        self.state[4] = ord(event[2])

    def on_connect(self, stat=None):
        if stat is not None:
            self.connected = stat

        m = self.messages[2]

        if self.btkservice is None:
            self.messages[2] = "No server"
        elif self.connected:
            self.messages[2] = "Connected"
        else:
            self.messages[2] = "Disconnected"

        if m != self.messages[2]:
            print(self.messages[2])
            self.send_messages()

    def send_messages(self):
        if self.dev is None: return
        for (i,m) in enumerate(self.messages):
            self.dev.message_write(i, m[min(self.message_offset, (len(m)//8 - 1)*8):])

    #poll for keyboard events
    def check_mailbox(self):
        if self.dev is None: return
        try:
            try:
                msg = self.dev.message_read(8, 0, True)
                if msg[1] == b"BTNCENTER\0":
                    ip = subprocess.check_output("hostname -I", shell=True)
                    ssid = subprocess.check_output("iwgetid | sed -E 's/.*ESSID:\"(.*)\"/\\1/g'", shell=True)
                    self.messages[0] = ip
                    self.messages[1] = ssid
                    self.message_offset = 0
                    self.send_messages()
                elif msg[1] == b"BTNRIGHT\0":
                    self.message_offset = min(
                        self.message_offset+8,
                        max((len(m)//8 - 1)*8 for m in self.messages)
                    )
                    self.send_messages()
                elif msg[1] == b"BTNLEFT\0":
                    self.message_offset = max(
                        self.message_offset-8,
                        0
                    )
                    self.send_messages()
                else:
                    print("Unknown message")
                    print(msg)
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                ignore = [
                    "No active program",
                    "Specified mailbox queue is empty",
                ]
                if str(e) not in ignore:
                    print(e)
        finally:
            GLib.timeout_add(1000, self.check_mailbox)
    def check_buttons(self):
        if self.dev is None: return
        try:
            l = self.dev.b0.is_pressed()
            r = self.dev.b1.is_pressed()
            if l != self.l or r != self.r:
                self.l = l
                self.r = r
                if self.iface is not None:
                    #print((l, r))
                    pass
                self.state[4] = 0
                if l and not r:
                    self.state[4] = ord("P")
                if r and not l:
                    self.state[4] = ord("O")
                self.send_input()
        finally:
            GLib.idle_add(self.check_buttons)

    #forward keyboard events to the dbus service
    def send_input(self):
        if self.iface is None:
            return

        bin_str=""
        element=self.state[2]
        for bit in element:
            bin_str += str(bit)

        #print(self.state)
        self.iface.send_keys(int(bin_str,2),self.state[4:10])

from nxt.brick import FileWriter
from nxt.error import FileNotFound
from nxt.utils import parse_command_line_arguments

def _write_file(b, fname, data):
    w = FileWriter(b, fname, len(data))
    print('Pushing %s (%d bytes) ...' % (fname, w.size), end=' ')
    sys.stdout.flush()
    w.write(data)
    print('wrote %d bytes' % len(data))
    w.close()

def write_file(b, fname):
    f = open(fname, 'rb')
    data = f.read()
    f.close()
    try:
        b.delete(fname)
        print('Overwriting %s on NXT' % fname)
    except FileNotFound:
        pass
    _write_file(b, fname, data)

def thread_fn(brick):
    last_ip = None
    def get_ip():
        time.sleep(5)
        return subprocess.check_output("hostname -I", shell=True)
    while True:
        try:
            ip = get_ip()
            if ip != last_ip:
                last_ip = ip
                subprocess.check_call("./ip.sh", shell=True)
                try:
                    brick.stop_program()
                except:
                    pass
                write_file(brick, 'ip.rxe')
                brick.start_program('ip.rxe')
        except Exception as e:
            print(e)
            time.sleep(30)

def main():
    while True:
        print("Setting up keyboard")

        DBusGMainLoop(set_as_default=True)
        kb = Keyboard()

        #_thread.start_new_thread(thread_fn, (kb.dev,))
        print("main loop")
        GLib.idle_add(kb.check_buttons)
        GLib.idle_add(kb.check_mailbox)
        GLib.MainLoop().run()

if __name__ == "__main__":
    main()
