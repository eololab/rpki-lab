#!/usr/bin/env python3

import sys
import time
import struct
import socket

messages = []
messages.append('announce route 66.185.112.0/24 next-hop self as-path [174,2914,42]')
messages.append('announce route 144.41.0.0/16 next-hop self as-path [174,553]')
messages.append('announce route 193.16.4.0/22 next-hop self as-path [174,1299,680]')
messages.append('announce route 23.162.96.0/24 next-hop self as-path [174]')
messages.append('announce route 1.36.160.0/19 next-hop self as-path [174]')
messages.append('announce route 131.196.192.0/24 next-hop self as-path [174 16735 16735 28158 1]')
messages.append('announce route 194.20.8.0/21 next-hop self as-path [8968 3313]')
messages.append('announce route 151.17.0.0/16 next-hop self as-path [8968 1267]')
messages.append('announce route 211.13.0.0/17 next-hop self as-path [1299 2518 2518]')

for message in messages:
    sys.stdout.write(message + '\n')
    sys.stdout.flush()

while True:
    time.sleep(1)
