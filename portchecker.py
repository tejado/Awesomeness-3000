#!/usr/bin/env python
#
# ./portchecker.py
# C:\Python27\python.exe "C:\Users\user\Desktop\Stuff\portchecker.py"

import sys
import os
import socket
import errno
import csv
import re

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# timeout in seconds
timeout = 5

# if set to True, ECONNREFUSED will be interpreted as "port is open but no listening service"
# otherwise it will be interpreted as a closed one
connref_is_open = True

#create rules array
rules_dict = {}

##
# Format:
#   rule_id ; description ; target_address;  port_1 ; port_2 ; port_3 ; port_n 
#
# target_address can be IPv4 or IPv6 (hostnames are IPv4)
#
# The port is default interpreted as tcp but can be changed to udp with a "/udp" suffix, e.g. 123/udp
# UDP mode is experimental - not verified if its working correctly.

#You can also use a .csv file and use that as an argument like this: python portchecker.py filename.csv
#However, it still needs to have ; as the delimiter.
rules_csv = """
10; Internet - google.net; www.google.net; 80; 443
"""

# Example CSV
# rules_csv = """
# 1; Localhost Hostname test; localhost; 80; 443
# 1; Localhost IPv4 test; 127.0.0.1; 80; 443
# 1; Localhost IPv6 test; ::1; 80; 443
# 10; Spacewalk Server 1; 10.0.0.1; 80; 443; 5222
# 10; Spacewalk Server 2; 2001:0db8:85a3:08d3:1319:8a2e:0370:7347; 80; 443; 5222
# 30; NTP #2; 192.168.1; 123/udp
# 30; NTP #2; 192.168.1; 123/udp
# 99; Internet; www.google.net; 80; 443
# 99; API Server; api-server.somehost.net; 80; 443
# 100; test; hostname.does.not.exist; 80; 443
# """



# as we don't want to have non-standard packages in this portchecker, ipv6 address will be validated per regex
# http://stackoverflow.com/a/319293
def is_valid_ipv6(ip):
    pattern = re.compile(r"^\s*(?!.*::.*::)(?:(?!:)|:(?=:))(?:[0-9a-f]{0,4}(?:(?<=::)|(?<!::):)){6}(?:[0-9a-f]{0,4}(?:(?<=::)|(?<!::):)[0-9a-f]{0,4}(?:(?<=::)|(?<!:)|(?<=:)(?<!::):)|(?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)){3})\s*$", 
    re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None

# natural number ordering of lists
# http://stackoverflow.com/a/4836734
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

def create_rules_dict(reader) :
    for row in reader:
        if not row:
            continue
        rule_id = row[0].strip()
        if rule_id not in rules_dict:
            rules_dict[rule_id] = {'desc': row[1].strip()}
        rules_dict[rule_id][row[2].strip()] = row[3:]
    

print("")
print( "Awesomenes Portchecker 3000" )
print( "---------------------------" )
if len(sys.argv) > 1:
    try:
        if os.stat(sys.argv[1]).st_size < 1:
            raise Exception('Please put contents in the file.')
    except Exception as error:
        print(repr(error))
        
    with open(sys.argv[1]) as f:
        reader = csv.reader(f, delimiter=';')
        create_rules_dict(reader)
else:
    try:
        f = StringIO(rules_csv)
        reader = csv.reader(f, delimiter=';')
        create_rules_dict(reader);
    except NameError:
        print("Please define the rules_csv variable")

rules_keys = natural_sort(rules_dict.keys())
for rule_id in rules_keys:
    rule = rules_dict[rule_id]
    
    print("")
    print( "#%s - %s" % (rule_id, rule['desc']) )
    print("")
    
    del(rules_dict[rule_id]['desc'])
    
    i = 0
    j = 0
    for target in rule.items():
        target = str(target[0].strip())
        if is_valid_ipv6(target):
            if socket.has_ipv6:
                addr_family = socket.AF_INET6
                addr_family_info = " (IPv6)"
            else:
                print( "No IPv6 support on this platform" )
                continue
        else:
            addr_family = socket.AF_INET
            addr_family_info = " (IPv4)"
       
        print( "\tDestination%s: %s" % (addr_family_info, target) )
        for port in rule[target]:
            i += 1
            port = port.strip()
            
            # UDP
            if port.endswith("/udp"):
                port = port.strip("/udp") 
                
                if not port.isdigit():
                    print("\t\tPort (%s) is not a number... SKIP" % (port))
                    continue

                print("\t\tPort %6s (UDP)..." % (port)),
                
                sock = socket.socket(addr_family, socket.SOCK_DGRAM)
                sock.settimeout(timeout)
                
                try:
                    sock.sendto("--PING--", (target, int(port)))
                    recv, svr = sock.recvfrom(255)
                except Exception as e:
                    try: err, errtxt = e
                    except ValueError:
                        result = 0
                    else:
                        result = errno.EAGAIN
            # TCP         
            else:
                if not port.isdigit():
                    print("\t\tPort (%s) is not a number... SKIP" % (port))
                    continue
            
                sys.stdout.write("\t\tPort \t%6s..." % (port))
                sys.stdout.flush()
            
                sock = socket.socket(addr_family, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                try:
                    result = sock.connect_ex((target,int(port)))
                except socket.gaierror:
                    result = -1
 
            if result == 0:
                j += 1
                print("open")
            elif result == errno.ECONNREFUSED and connref_is_open == True:
                j += 1
                print("open (NO SERVICE)")
            elif result == errno.EAGAIN or result == errno.EWOULDBLOCK or result == errno.ECONNREFUSED:
                print("closed") 
            elif result == errno.EHOSTUNREACH:
                print("no route to host")
            elif result == -1:
                print("hostname resolution error")
            else:
                print("UNKNOWN error (%i - %s)" % (result, os.strerror(result))) 
            sys.stdout.flush()
        print("")
        
    sys.stdout.write("    Guru-Meter:  ")
    sys.stdout.flush()
    if j == 0:
        print("BAAAAAD - rule is completly missing...")
    elif i > j:
        print("Mhhh?? Try again! Some ports seems to be missing")
    else:
        print("ACHIEVEMENT FIREWALLGURU-%s UNLOCKED - rule is implemented" % rule_id)
    print("")
