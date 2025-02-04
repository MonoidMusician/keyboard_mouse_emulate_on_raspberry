#!/usr/bin/python3
#
# nxt_push program -- Push a file to a LEGO Mindstorms NXT brick
# Copyright (C) 2006  Douglas P Lau
# Copyright (C) 2010  rhn
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import sys
import nxt.locator
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

if __name__ == '__main__':
    arguments, keyword_arguments = parse_command_line_arguments(sys.argv)

    if '--help' in arguments:
        print('''nxt_push -- Push a file to a LEGO Mindstorms NXT brick
Usage:  nxt_push [--host <macaddress>] <file>''')
        exit(0)
    
    brick = nxt.locator.find_one_brick(keyword_arguments.get('host',None))
    brick.stop_program()
    for filename in arguments:
        write_file(brick, filename)
        if len(arguments) == 1:
            brick.start_program(filename)
    brick.sock.close()
