#!/bin/bash

nbc -sm- -D=TEXT="\"$(hostname -I)\"" -D=DATE="\"$(date +"%H:%M:%S %Z")\"" -O=ip.rxe ip.nxc
