#!/usr/bin/env python3
# encoding: utf8

import math
import requests
r = requests.get('https://ftp.apnic.net/stats/apnic/delegated-apnic-extended-latest')

for line in r.iter_lines():
    line = line.decode( 'utf8' )
    if (('ipv4' in line) & ('CN' in line)):
        s=line.split("|")
        net=s[3]
        cidr=float(s[4])
        print( "%s/%d" % (net,(32-math.log(cidr,2))) )
