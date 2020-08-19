
# Proof-of-concept code for reading data from a Wifi microscope.
# See https://www.chzsoft.de/site/hardware/reverse-engineering-a-wifi-microscope/.

# Copyright (c) 2020, Christian Zietz <czietz@gmx.net>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time
import socket
import msvcrt

HOST = "192.168.29.1"	# Microscope hard-wired IP address
SPORT = 20000			# Microscope command port
RPORT = 10900			# Receive port for JPEG frames
o = None

# Open command socket for sending
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
	# s.sendto(b"JHCMD\xd0\x00", (HOST, SPORT))
	# Send commands like naInit_Re() would do
	s.sendto(b"JHCMD\x10\x00", (HOST, SPORT))
	s.sendto(b"JHCMD\x20\x00", (HOST, SPORT))
	# Heartbeat command, starts the transmission of data from the scope
	s.sendto(b"JHCMD\xd0\x01", (HOST, SPORT))
	s.sendto(b"JHCMD\xd0\x01", (HOST, SPORT))

	# Open receive socket and bind to receive port
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as r:
		r.bind(("", RPORT))
		r.setblocking(0)
		# Note: Modify this line if not running under Windows
		while not msvcrt.kbhit():
			try:
				data = r.recv(1450)
				if len(data) > 8:
					# Header
					framecount = data[0] + data[1]*256
					packetcount = data[3]
					print("Frame %d, packet %d" % (framecount, packetcount))
					# Data
					if packetcount==0:
						# A new frame has started, open a new file
						if o is not None:
							o.close()
						# Only save 100 frames to avoid filling up the disk
						o = open("frame_%d.jpg" % (framecount%100), "wb")
						# Send a heartbeat every 50 frames (arbitrary number) to keep data flowing
						if framecount%50 == 0:
							s.sendto(b"JHCMD\xd0\x01", (HOST, SPORT))
					o.write(data[8:])
			except:
				time.sleep(0.01)
	# Stop data command, like in naStop()
	s.sendto(b"JHCMD\xd0\x02", (HOST, SPORT))
