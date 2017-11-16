#!/usr/bin/env python3
# encoding: utf8

import os
import sys
import time
import traceback
import json
import argparse
import itertools
import hashlib
import uuid
from pprint import pprint

import requests
import subprocess
import pathlib

def filemonitor( filepath ):
    f = open( filepath )
    while 1:
        where = f.tell()
        line = f.readline()
        if not line or line.find('\n')==-1:
            time.sleep(1)
            f.seek(where)
        else:
            yield line

def masscan( cidr, port, rate=100, callback=print ):
    masscan_output_dirpath = '/tmp/masscanresult/'
    pathlib.Path( masscan_output_dirpath ).mkdir( parents=True, exist_ok=True )
    masscan_output_filename = str( uuid.uuid4() )
    masscan_output_filepath = os.path.join( masscan_output_dirpath, masscan_output_filename )
    with open( masscan_output_filepath, 'wb' ) as fout:
        pass

    masscan_args = [    
                        'masscan',
                        str(cidr),
                        '-p', str(port),
                        '--output-format', 'json',
                        '--output-filename', masscan_output_filepath,
                        '--rate', str(rate),
                    ]
    masscan_process = subprocess.Popen( masscan_args )

    for line in filemonitor( masscan_output_filepath ):
        # masscan json output line format:
        # {   "ip": "180.97.235.167",   "ports": [ {"port": 80, "proto": "tcp", "status": "open", "reason": "syn-ack", "ttl": 55} ] },
        try:
            record = json.loads( line.strip()[:-1] )
            callback( record['ip'] )
        except:
            print( traceback.format_exc() )
            continue

def check_solr( ip ):
    try:
        url = 'http://{}:8983/solr/'.format( ip )
        r = requests.get( url, timeout=3 )
        if r.status_code==200:
            with open( 'good.txt', 'a' ) as fout:
                fout.write( 'http://{}:8983/solr/\n'.format( ip ) )
        else:
            print( 'not 200 status code for url:', url )
    except:
        print( traceback.format_exc() )
        return
        
def main():
    with open( 'cidr_china.txt' ) as fin:
        cidr_list = fin.readlines()
    cidr_list = [ x.strip() for x in cidr_list ]
    cidr = ','.join( cidr_list )

    rate = int( sys.argv[1] )

    masscan( cidr, 8983, rate=rate, callback=check_solr )

if __name__ == '__main__':
    main()
