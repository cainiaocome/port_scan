#!/usr/bin/env python2
# encoding: utf8

import sys
import threading
from Queue import Queue
import time
import socket
import struct

socket.setdefaulttimeout( 2 )

print_lock = threading.Lock()

def cidr_to_generator( cidr ):
    (ip, cidr) = cidr.split('/')
    cidr = int(cidr)
    host_bits = 32 - cidr
    i = struct.unpack('>I', socket.inet_aton(ip))[0] # note the endianness
    start = (i >> host_bits) << host_bits # clear the host bits
    end = i | ((1 << host_bits) - 1) 

    i = start
    while i<end:
        yield socket.inet_ntoa(struct.pack('>I',i))
        i = i + 1

cidr = sys.argv[1]
ports = sys.argv[2].split( ',' )
ports = list( filter( None, ports ) )
ports = list( map( lambda port: int( port ), ports ) )

def portscan(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        con = s.connect((ip,port))
        with print_lock:
            print(ip,port, 'open')
        con.close()
    except:
        sys.exc_clear()


# The threader thread pulls an worker from the queue and processes it
def threader():
    while True:
        job = q.get()
        ip, port = job
        portscan( ip, port )

        # completed with the job
        q.task_done()

q = Queue( 1024 )

for x in range( 512 ):
     t = threading.Thread(target=threader)
     t.daemon = True
     t.start()

start = time.time()

for port in ports:
    for ip in cidr_to_generator( cidr ):
        job = ( ip, port )
        q.put( job )

# wait until the thread terminates.
q.join()