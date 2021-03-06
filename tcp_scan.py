#!/usr/bin/env python3
# encoding: utf8
"""
    author: jlz
    last modify: 20170402
    use: port scan, tcp only for now
    todo: fix single ip scan
"""

import os
import socket
import sys
import json
import uuid
import time
import random
import queue
import string
import logging
import traceback
import threading
import argparse
from pprint import pprint, pformat

import netaddr
import gevent
from gevent import monkey
monkey.patch_all()

import j_pentest_utils

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

class Random_IP_Generator( object ):
    def __init__( self, args ):
        if not os.path.exists( args.ip ):
            self.ip_range_list = [ iter(netaddr.IPNetwork(args.ip)), ]
            return
        with open( args.ip, 'r' ) as f:
            lines = f.readlines()
        cidrs = [ line.strip() for line in lines if not line.startswith( '#' ) ]
        self.ip_range_list = [ iter(netaddr.IPNetwork( cidr )) for cidr in cidrs ]
        
    def get_random_ip( self ):
        ip_range = random.choice( self.ip_range_list )
        try:
            #next_ip = ip_range.next()
            next_ip = next( ip_range )
            if next_ip.is_private() or next_ip.is_netmask() or next_ip.is_multicast() or next_ip.is_reserved():
                #return None
                return str( next_ip )
            else:
                return str( next_ip )
        except StopIteration:
            self.ip_range_list.remove( ip_range )
            return None
        
    def get_random_ip_list(self, count=1):
        result_ip_list = []
        for i in range( count ):
            random_ip = self.get_random_ip()
            if random_ip:
                result_ip_list.append( random_ip )
        return result_ip_list

def tcp_check( ip, port, timeout=1 ):
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    s.settimeout( timeout )
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.connect( ( ip, port ) )
        con_status = True
    except:
        con_status = False
    finally:
        s.close()
        return con_status

class PortScanFactory( j_pentest_utils.BaseFactory ):

    def do_job( self, job ):
        ip, port, timeout = job['ip'], job['port'], job['timeout']
        try:
            if tcp_check( ip, port, timeout ):
                print( ip, port, 'open' )
                success_record = {
                    'ip': str(ip),
                    'port': port,
                }
                self.success_queue.put( success_record )
            else:
                print( ip, port, 'closed' )
        except Exception as e:
            print ( e.args )

    def manager( self ):
        random_ip_generator = Random_IP_Generator( self.args )
        while True:
            random_ip_list = random_ip_generator.get_random_ip_list()
            for ip in random_ip_list:
                for port in parseIntSet(self.args.port):
                    job = {
                        'ip': str(ip),
                        'port': port,
                        'timeout': self.args.timeout,
                    }
                    self.job_queue.put( job )

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument( '-p', '--port', type=str, required=True, help='port to scan(example:22, 1-33)' )
    argparser.add_argument( '-i', '--ip', type=str, required=True, help='file with cidr to scan(or ip address)' )
    argparser.add_argument( '-o', '--output', type=str, default='good.txt', required=False, help='output file, default good.txt' )
    argparser.add_argument( '-t', '--thread', type=int, default=32, required=False, help='thread count to spawn, default 32' )
    argparser.add_argument( '--timeout', type=int, default=1, required=False, help='tcp connection create timeout, default 1' )
    args = argparser.parse_args()

    portscanfactory = PortScanFactory( args )

    while True:
        time.sleep( 3 )

if __name__ == '__main__':
    main()
