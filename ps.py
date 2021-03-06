#!/usr/bin/env python2
# encoding: utf8

import sys
import threading
from Queue import Queue
import time
import socket
import struct
import traceback

socket.setdefaulttimeout( 2 )

print_lock = threading.Lock()

def parseIntSet(nputstr=""):
    # return a set of selected values when a string in the form:
    # 1-4,6
    # would return:
    # 1,2,3,4,6
    # as expected...
    selection = set()
    invalid = set()
    # tokens are comma seperated values
    tokens = [x.strip() for x in nputstr.split(',')]
    for i in tokens:
        if len(i) > 0:
            if i[:1] == "<":
                i = "1-%s"%(i[1:])
        try:
            # typically tokens are plain old integers
            selection.add(int(i))
        except:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by a dash
                    # try to build a valid range
                    first = token[0]
                    last = token[len(token)-1]
                    for x in range(first, last+1):
                        selection.add(x)
            except:
                # not an int and not a range...
                invalid.add(i)
    # Report invalid tokens before returning valid selection
    if len(invalid) > 0:
        print ( "Invalid set: " + str(invalid) )
    return selection

# end parseIntSet
def cidr_to_generator( cidr ):
    (ip, cidr) = cidr.split('/')
    cidr = int(cidr)
    if cidr==32:
        yield ip
        return
    host_bits = 32 - cidr
    i = struct.unpack('>I', socket.inet_aton(ip))[0] # note the endianness
    start = (i >> host_bits) << host_bits # clear the host bits
    end = i | ((1 << host_bits) - 1) 

    i = start
    while i<end:
        yield socket.inet_ntoa(struct.pack('>I',i))
        i = i + 1

cidr = sys.argv[1]
ports = parseIntSet( sys.argv[2] )

def portscan(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        con = s.connect((ip,port))
        with print_lock:
            print(ip,port, 'open')
        con.close()
    except socket.timeout, socket.error:
        sys.exc_clear()
    except:
        #traceback.print_exc()
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

for x in range( 32 ):
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
