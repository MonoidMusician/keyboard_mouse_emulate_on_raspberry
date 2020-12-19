#!/bin/bash

nbc -sm- -O=messages.rxe messages.nxc && ../spy.sh <<< 'import nxt; import nxt.bluesock; b = nxt.bluesock.BlueSock("00:16:53:0A:FB:79").connect(); import ip; ip.write_file(b, "messages.rxe")'
