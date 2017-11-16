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

import subprocess
import pathlib
from pprint import pprint

from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring
import requests

def do_masscan( cidr, port, outputformat, outputfilename, rate=1000 ):
    masscan_args = [    
                        'masscan',
                        str(cidr),
                        '-p', str(port),
                        '--output-format', outputformat,
                        '--output-filename', outputfilename,
                        '--rate', str(rate),
                    ]
    masscan_process = subprocess.run( masscan_args )

def masscan( cidr, port, rate=1000 ):
    masscan_output_dirpath = '/tmp/masscanresult/'
    pathlib.Path( masscan_output_dirpath ).mkdir( parents=True, exist_ok=True )
    masscan_output_filename = str( uuid.uuid4() )
    masscan_output_filename = os.path.join( masscan_output_dirpath, masscan_output_filename )
    do_masscan( cidr, port, 'xml', masscan_output_filename, rate )

    ip_list = []

    try:
        scanresult = bf.data( fromstring( open( masscan_output_filename ).read() ) )
    except:
        pass
    else:
        for x in scanresult['nmaprun']['host']:
            ip = x['address']['@addr']
            ip_list.append( ip )
        
    return ip_list

def main():
    with open( 'cidr_china.txt' ) as fin:
        cidr_list = fin.readlines()
    cidr_list = [ x.strip() for x in cidr_list ]

    for cidr in cidr_list:
        ip_list = masscan( cidr, 8983, rate=100 )

        for ip in ip_list:
            try:
                url = 'http://{}:8983/solr/'.format( ip )
                r = requests.get( url, timeout=3 )
            except:
                continue
                
            if r.status_code==200:
                with open( 'good.txt', 'a' ) as fout:
                    fout.write( 'http://{}:8983/solr/\n'.format( ip ) )

if __name__ == '__main__':
    main()
