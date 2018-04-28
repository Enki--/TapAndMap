#!/usr/bin/env python
# This script picks a random octet, and sends a ping to it.

import subprocess
import time
import random
timeout = 1 #  this is in seconds
numberpackets = 9999  #This is the number of packets to send
import os
import socket
import math
import string

send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

i = 1
while (i <= numberpackets):
	A = random.randint(6,220)
	B = random.randint(6,200)
	C = random.randint(6,200)
	D = random.randint(6,200)
	address = str(A) + "." + str(B) + "." + str(C) + "." + str(D)
	print str(i) + ": Sending a packet to: " + address
	send_sock.sendto("A", (address, 10000))
	i = i + 1
	time.sleep(timeout)
print "done"
