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
import random
from pprint import pprint

from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring

import requests

def main():
    scanresult = bf.data( fromstring( open(sys.argv[1]).read() ) )

    print( type( scanresult ) )

    for x in scanresult['nmaprun']['host']:
        ip = x['address']['@addr']
    
        try:
            url = 'http://{}:8983/solr/'.format( ip )
            r = requests.get( url, timeout=3 )
        except:
            continue
            
        if r.status_code==200 or r.status_code==302:
            print( ip )
            print( 'solr found' )
            print( '-'* 30 )

if __name__ == '__main__':
    main()
