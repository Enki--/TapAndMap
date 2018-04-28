#!/usr/bin/python

''' 
This script sniffs a bridge interface between two USB ports from a Raspberry Pi V2 b or from a Pi V 3. 
The bridge could connect a PC to a router, or a router to a modem, or whatever you act, and it will act as a switch
Alternatively, it will sniff a bridge connecting just one USB dongle attached to a hub or spanning port or tap.  
It ignores any private or multicast addresses, and concentrates on public addresses.
It finds the location and coordinates of non-private IPs, and saves that info in the log file:
<date/time>_Connection_log.txt.   This log will be split based on a TapAndMap.conf file entered user value.
This script will also update the /var/www/right.html website, so packet src/dst IP/port and location can be printed.
It will also update a JSON file for google maps to plot lines from the user-entered location, to the public locations.
This file needs to have the 'refresh' button on the browser pressed to see updates.  Next step is WebSockets to 
dynamically update the text on the right pane as well as on the GoogleMaps API. 
Note: that because the TapAndMap application is using GoogleMaps, this code will ignore Google IP addresses
as such, any traffic to google, even pings and such, will be intentionally ignored.
Remember to edit the TapAndMap.conf file for your preferences (home location, log roll time, etc)

Changelog:
Ver1.0 had Server Sent Evenets, but this ended up causing issues with the browser not clearing, so I removed it.
Ver1.1 was stable without SSE (you now have to hit the refresh button to refresh the screen again).
Ver1.2 was a failed attempt to try to replace SSE with WebSockets.
Ver1.3 was an addition of the 'clear text' button (now there's clear map and clear text).
Ver1.3.2 checks for bad coordinates from MaxMind (sometimes they spit out text, not lat longs, which kills the JSON file)
'''

import os      						# needed to read and write from files
import socket						# needed to sniff
from struct import *
import time 						# needed to put time on packets
import pcapy						# needed to sniff
import sys
import subprocess    				#needed to run bash commands
import threading                    # needed to check the JSON file every 5 seconds
import string

cid = 0  # This is the connection ID.... it should increment with every packet parsed
PointList = []
numbpreviouslines = 0
ptime = time.strftime("%y.%m.%d.%H.%M.%S")
LogTime = time.time()
print "LogTime is " + str(LogTime)
filename = "/var/www/logs/20" + str(ptime) + "_Connection_log.txt"
checkfile1 = "touch " + filename      #Just making sure the file is there
ps = subprocess.Popen(checkfile1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print "Start time is: 20" + ptime   

startfile = "echo '0' > /var/www/JSONChanged.txt" 
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def CheckJsonBoolean (): 
    #print "Checking the JSONChanged.txt file"
    threading.Timer(5, CheckJsonBoolean).start ()
    JBool=open('/var/www/JSONChanged.txt','r')
    Jcontents = JBool.readlines()
    JBool.close()
    if Jcontents[0] == "1\n":
        #print "Clear Map Button has been pressed... deleting Points from RAM"
        startfile = "echo '0' > /var/www/JSONChanged.txt"
        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        del PointList[:]
CheckJsonBoolean()

# Read in variables from config file
configfile=open('/var/www/TapAndMap.conf','r')
contents = configfile.readlines()
configfile.close()
homelat = contents[5]
homelat = homelat[homelat.find('{')+1:homelat.rfind('}')]
print "homelat is: " + homelat
homelong = contents[6]
homelong = homelong[homelong.find('{')+1:homelong.rfind('}')]
print "homelong is: " + homelong
hometime = contents[10]
hometime = hometime[hometime.find('{')+1:hometime.rfind('}')]
print "hometime is: " + hometime
ipaddr = contents[13]
ipaddr = ipaddr[ipaddr.find('{')+1:ipaddr.rfind('}')]
print "ipaddr is: " + ipaddr
zoomlevel = contents[16]
zoomlevel = zoomlevel[zoomlevel.find('{')+1:zoomlevel.rfind('}')]
print "zoomlevel is: " + zoomlevel 
RFont = contents[19]
RFont = RFont[RFont.find('{')+1:RFont.rfind('}')]
print "Right Font Size is: " + RFont
RightPacketLines = contents[22]
RightPacketLines = RightPacketLines[RightPacketLines.find('{')+1:RightPacketLines.rfind('}')]
print "Number of packets to disply on the right pane is: " + RightPacketLines
RefreshRate = contents[25]
RefreshRate = RefreshRate[RefreshRate.find('{')+1:RefreshRate.rfind('}')]
print "Refresh Rate of Right Pane is: " + RefreshRate
LogRun = contents[28]
LogRun = LogRun[LogRun.find('{')+1:LogRun.rfind('}')]
print "Log will run for " + LogRun + " minutes before splitting"
IPsToIgnore = contents[33]
IPsToIgnore = IPsToIgnore[IPsToIgnore.find('{')+1:IPsToIgnore.rfind('}')]
IgnoreIPValues = IPsToIgnore.split(" ")
print "IPs to ignore are: " + IPsToIgnore
chksrc = ""
chkdst = ""
for item in IgnoreIPValues:
    chksrc = chksrc + 'src.startswith("' + item + '") or ' 
    chkdst = chkdst + 'dst.startswith("' + item + '") or ' 
srclen = len(chksrc)
dstlen = len(chkdst)
chksrc = chksrc[0:srclen - 3]
chkdst = chkdst[0:dstlen - 3]
#print "chksrc line is: " + chksrc + '\n'
#print "chkdst line is: " + chkdst + '\n'

# Update index.html file with the config variables found above
configfile=open('/var/www/index_template.html','r')
contents = configfile.readlines()
configfile.close()
contents[50]='var myLocation=new google.maps.LatLng(' + homelat + ',' + homelong + '); var opt = {minZoom: 2};' + '\n'
contents[83]='    window.open(' + '"' + 'http:' + '/' + '/' + ipaddr + '/cgi-bin/ResetScreen.sh' + '"' + ', ' + "'" + '_blank' + "');"   + '\n'
contents[116]='    window.open(' + '"' + 'http:' + '/' + '/' + ipaddr + '/cgi-bin/ResetText.sh' + '"' + ', ' + "'" + '_blank' + "');"   + '\n'
contents[124]='    zoom:' + zoomlevel + ','+ '\n'
contents="".join(contents)
newfile=open('/var/www/tmpfile', 'w')
newfile.write(contents)
newfile.close()
startfile = "mv /var/www/tmpfile /var/www/index.html" 
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
ps.wait()

# Update the right.html file with the font size value specified in the above config file
configfile2=open('/var/www/right_template.html','r')
contents2 = configfile2.readlines()
configfile2.close()
contents2[9] = contents2[9][:14] + RFont + contents2[9][16:]
#contents2[9] = 'p     {font-size: ' + RFont + '%; display:inline}' + 
contents2="".join(contents2)
newfile2=open('/var/www/tmpfile2', 'w')
newfile2.write(contents2)
newfile2.close()
startfile2 = "mv /var/www/tmpfile2 /var/www/right.html" 
ps = subprocess.Popen(startfile2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
ps.wait()

# Start with a blank points_and_lines.json file
startfile = "cp /var/www/Connections_Seen_Template.json /var/www/Connections_Seen.json" 
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
startfile = "cp /var/www/right_template.html /var/www/right.html"
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
startfile = "chown -R www-data /var/www"   #need to change privs to www-data so that the web user can clear the screen
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
startfile = "chgrp -R www-data /var/www"   #need to change privs to www-data so that the web user can clear the screen
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
startfile = "chmod 666 /var/www/*.html" 
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
startfile = "chmod 666 /var/www/Connections_Seen.json" 
ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
ps.wait()

# Sometimes MaxMind gives crap instead of lat/longs.  This checks to make sure it's a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def CheckForLogSplit (): 
    threading.Timer(20, CheckForLogSplit).start ()  # Check every 20 seconds for log timer to split log based on config file setting
    global LogTime
    global filename
    if LogTime  + (int(LogRun) * 60) < time.time():   # number of minutes for log to run before splitting based on config file.     CHANGE ME TO 3600.... for now, I'll make it 300, which is 5 minutes
        # Read in the last log file and create a JSON file and a html file with that time based on map_template.html  
        # read in log file
        lastlogfile=open(filename,'r')
        logcontents = lastlogfile.readlines()
        lastlogfile.close()
        # parse the log file and create a JSON file
        JSONtemplate = open('/var/www/Connections_Seen_Template.json','r')
        newjsonfile = JSONtemplate.readlines()
        JSONtemplate.close()
        temppointlist=[]
        for line in logcontents:
            currentline = line.split(",")
            #print "value 0 of log is " + currentline[0] + " value 1 of log is " + currentline[1] + " value 2 of log is " + currentline[2] + " value 3 of log is " + currentline[3] + " value 4 of log is " + currentline[4] + " value 5 of log is " + currentline[5] + " value 6 of log is " + currentline[6] + " value 7 of log is " + currentline[7] + " value 8 of log is " + currentline[8] + " value 9 of log is " + currentline[9] + " value 10 of log is " + currentline[10] + " value 11 of log is " + currentline[11] + " value 12 of log is " + currentline[12] + "\n"
            if currentline[6] == homelong and currentline[5] == homelat:
                slat = homelat
                slong = homelong
                dlat = currentline[7]
                dlong = currentline[8]
            else:
                slat = currentline[7]
                slong = currentline[8]
                dlat = currentline[5]
                dlong =currentline[6]
            if not (dlat in temppointlist and dlong in temppointlist and temppointlist.index(dlat) + 1 == temppointlist.index(dlong) or (currentline[9] == "IP Unknown") or (not(is_number(dlat)) or (not(is_number(dlong))) or (not(is_number(slong))) or (not(is_number(slat))))):
                temppointlist.append(dlat)
                temppointlist.append(dlong)
                ziplen = len(currentline[12])
                zipval = currentline[12]
                if ziplen < 2:
                    ziplen = 3
                    zipval = "N/A"
                newjsonfile.insert(4, '     {\n')
                newjsonfile.insert(5, '        "type": "Feature",\n')
                newjsonfile.insert(6, '        "geometry": {\n')
                newjsonfile.insert(7, '           "type": "Point",\n')
                newjsonfile.insert(8, '           "coordinates": [' + dlong + ',' + dlat + ']' + '\n')
                newjsonfile.insert(9, '           },' + '\n')
                newjsonfile.insert(10, '        "properties": {\n')
                newjsonfile.insert(11, '           "description":  "' +  currentline[2] + ' to ' + currentline[3] + ', '  + currentline[9] + ', ' + currentline[10] + ', ' + currentline[11] + ", " + zipval[0:ziplen -1] + '",\n')
                if currentline[4] == "TCP":
                    color = 'red'
                elif currentline[4] == "ICMP":
                    color = 'green'
                elif currentline[4] == "UDP":
                    color = 'blue'
                newjsonfile.insert(12, '           "color": "' + color + '"\n')
                newjsonfile.insert(13, '           }\n')
                newjsonfile.insert(14, '        },\n')
                newjsonfile.insert(15, '\n')
                newjsonfile.insert(16, '     {\n')
                newjsonfile.insert(17, '        "type": "Feature",\n')
                newjsonfile.insert(18, '        "geometry": {\n')
                newjsonfile.insert(19, '           "type": "LineString",\n')
                newjsonfile.insert(20, '           "coordinates": [[' + currentline[6] + ',' + currentline[5] + '], [' + currentline[8] + ',' + currentline[7] + ']]\n')
                newjsonfile.insert(21, '           },' + '\n')
                newjsonfile.insert(22, '        "properties": {\n')
                newjsonfile.insert(23, '           "description":  "' +  currentline[2] + ' to ' + currentline[3] + ', '  + currentline[9] + ', ' + currentline[10] + ', ' + currentline[11] + ', ' +  zipval[0:ziplen -1] + '",\n')
                newjsonfile.insert(24, '           "color": "' + color + '"\n')
                newjsonfile.insert(25, '           }' + '\n')
                newjsonfile.insert(26, '        }' + ', \n')
                newjsonfile.insert(27, '\n')
        newfilename = '/var/www/JSONFiles/20' + filename[16:33] + '.json' 
        newfile=open(newfilename, 'w')
        newjsonfile = "".join(newjsonfile)
        newfile.write(newjsonfile)
        newfile.close()
        # Now that json file is created with previous data, create a html file to call it
        MAPtemplate = open('/var/www/map_template.html','r')
        newmapfile = MAPtemplate.readlines()
        MAPtemplate.close()
        newmapfile[50]='var myLocation=new google.maps.LatLng(' + homelat + ',' + homelong + '); var opt = {minZoom: 2};' + '\n'
        newmapfile[73] = "    map.data.loadGeoJson('../JSONFiles/20" + filename[16:33] + ".json');"
        newfilename = '/var/www/maps/20' + filename[16:33] + '.html' 
        newfile=open(newfilename, 'w')
        newmapfile = "".join(newmapfile)
        newfile.write(newmapfile)
        newfile.close()

        # now that json and html are created, split the log and start over
        newtime = time.strftime("%y.%m.%d.%H.%M.%S")
        print "creating new log at 20" + str(newtime)
        filename = "/var/www/logs/20" + str(newtime) + "_Connection_log.txt"
        startfile = "touch filename"   #make a new log file
        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ps.wait()
        LogTime = time.time()
        cid = 0
        del temppointlist[:]
        startfile = "chown -R www-data /var/www"   
        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        startfile = "chgrp -R www-data /var/www"   
        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ps.wait()
CheckForLogSplit()

def main(argv):
	
	dev = "br0"
	cap = pcapy.open_live(dev , 65536 , 1 , 0)

	#start sniffing packets
	while(1) :
		(header, packet) = cap.next()
		#print ('%s: captured %d bytes, truncated to %d bytes' %(datetime.datetime.now(), header.getlen(), header.getcaplen()))
		parse_packet(packet)

#Convert a string of 6 characters of ethernet address into a dash separated hex string
def eth_addr (a) :
	b = "%.2x:%.2x:%.2x:%.2x:%.2x:%.2x" % (ord(a[0]) , ord(a[1]) , ord(a[2]), ord(a[3]), ord(a[4]) , ord(a[5]))
	return b

#function to parse a packet
def parse_packet(packet) :
	#parse ethernet header
	eth_length = 14
	eth_header = packet[:eth_length]
	eth = unpack('!6s6sH' , eth_header)
	eth_protocol = socket.ntohs(eth[2])
	#print 'Destination MAC : ' + eth_addr(packet[0:6]) + ' Source MAC : ' + eth_addr(packet[6:12]) + ' Protocol : ' + str(eth_protocol)

	#Parse IP packets, IP Protocol number = 8
	if eth_protocol == 8 :
		#Parse IP header
		#take first 20 characters for the ip header
		ip_header = packet[eth_length:20+eth_length]
		
		#now unpack them :)
		iph = unpack('!BBHHHBBH4s4s' , ip_header)

		version_ihl = iph[0]
		version = version_ihl >> 4
		ihl = version_ihl & 0xF

		iph_length = ihl * 4
                t = eth_length + iph_length

		ttl = iph[5]
		protocol = iph[6]
		s_addr = socket.inet_ntoa(iph[8]);
		d_addr = socket.inet_ntoa(iph[9]);
                srcport = "one"
                dstport = "two"

		#print 'Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(ttl) + ' Protocol : ' + str(protocol) + ' Source Address : ' + str(s_addr) + ' Destination Address : ' + str(d_addr)
                if (protocol == 6 or protocol == 1 or protocol == 17):       #It is TCP, ICMP, or UDP (we probably don't care about anything else)
                    srcport = " "
                    dstport = " "
                    ptime = time.strftime("%d/%m/%y %H:%M:%S")      
                    if (protocol == 6):
                        prototype = "TCP"
                        tcp_header = packet[t:t+20]
                        tcph = unpack('!HHLLBBHHH' , tcp_header)
                        sourceport = tcph[0]
                        destport = tcph[1] 
                        srcport = str(sourceport) 
                        dstport = str(destport)
#                        print "TCP Srcport: " + srcport + " Dsport: " + dstport
#                        print "Source port is: " + srcport + " Destinantion port is: "  + dstport
                    elif (protocol == 1):
                        prototype = "ICMP"
                        icmph_length = 4
                        icmp_header = packet[t:t+4]
                        icmph = unpack('!BBH' , icmp_header)
                        icmp_type = icmph[0]
                        srcport = str(icmp_type)
                        dstport = " " #icmp only has a type, so I blanked out the dst port
#                        print "ICMP Type: " + srcport + dstport
                    elif (protocol == 17):
                        prototype = "UDP"
                        udp_header = packet[t:t+8]
                        udph = unpack('!HHHH' , udp_header)
                        sourceport = udph[0]
                        destport = udph[1]
                        srcport = str(sourceport)
                        dstport = str(destport)
#                        print "UDP Srcport: " + srcport + " Dstport: " + dstport
                    src = str(s_addr)
                    dst = str(d_addr)
                    # It is OK to have two separate if statements below... a max of one will be from an external IP, so each may be parsed seperately
                    # 216.58.217. and 74.125.226. are Google Maps... We ignore this, as we are generating it.
                    #if not (src.startswith("209.85.") or src.startswith("172.217.") or src.startswith("209.85.202.") or src.startswith("64.233.") or src.startswith("8.8.8.") or src.startswith("216.58.") or src.startswith("173.194.") or src.startswith("74.125.") or (int(src.split(".")[0]) > 223 and int(src.split(".")[0]) < 240) or src.startswith("0.") or src.startswith("255.") or src.startswith("10.") or src.startswith("192.168.") or src.startswith("172.16.")):
                    if not (eval(chksrc)):
                        getcoords = "/usr/bin/geoiplookup -f /usr/local/share/GeoIP/GeoLiteCity.dat " + src
                        #print "running this: " + getcoords                        
                        global cid
                        cid = cid + 1   										#connection id.... increments per every packcet seen
                        ptime = time.strftime("%y.%m.%d.%H.%M.%S")				# packet time
                        ps = subprocess.Popen(getcoords, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out, err = ps.communicate()
                        country = out.split(":")[1]
                        country = country.split(",")[0]
                        try:
                            state = out.split(",")[2]
                        except IndexError:
                        	state = "NA"
                        try:
                            city = out.split(",")[3]
                        except IndexError:
                        	city = "NA"
                        try:
                            zip = out.split(",")[4]
                        except IndexError:
                        	zip = "NA"
                        try:
                            srclat = str(out.split(",")[6])
                        except IndexError:
                            srclat = "NA"
                        try:
                        	srclong = str(out.split(",")[7])   
                        except IndexError:
                        	srclong = "NA"
                        country = country[1:]
                        if country[0:20] == "IP Address not found":   # MaxMind doesn't know where this is
                            country = "IP Unknown"
                            state = " NA"
                            city = " NA" 
                            zip = " NA"
                        state = state[1:]
                        state = filter(lambda x: x in string.printable, state)
                        city = city[1:]
                        city = filter(lambda x: x in string.printable, city)
                        zip = zip[1:]
                        if len(zip) < 2:
                            zip = "N/A"
                        srclat = srclat[1:]
                        srclong =    srclong[1:]
                        dstlat = homelat
                        dstlong = homelong
                        #print "From SomeoneElse country is: " + country + " state is: " + state + " city is: " + city + " zip is: " + zip + " srclat is: " + srclat + "srclong is: " + srclong + " dstlat is: " + dstlat + "dstlong is: " + dstlong
                        stringtoappend = str(cid) + ",20" + str(ptime) + "," + src + ":" + srcport + "," + dst + ":" + dstport + "," + prototype + "," + srclat + "," + srclong + "," + dstlat + "," + dstlong + "," + country + "," + state + "," + city + "," + zip + "\n"
                        print stringtoappend
                        if prototype == "TCP":
                            color = 'red'
                        elif prototype == "ICMP":
                            color = 'green'
                        elif prototype == "UDP":
                            color = 'blue'
                        with open(filename, "a") as myfile:
                            myfile.write(stringtoappend)
                        #update JSON file if the point is unique
                        if not (srclat in PointList and srclong in PointList and PointList.index(srclat) + 1 == PointList.index(srclong) or (country == "IP Unknown")or (not(is_number(srclat)) or (not(is_number(srclong))))):
                            #print "Point: " + srclat + ", " + srclong + " is NOT the JSON file.  Adding it"
                            PointList.append(srclat)
                            PointList.append(srclong)
                            global numbpreviouslines 
                            numbpreviouslines= numbpreviouslines + 25 # 29 lines below, plus I write over 0-3
                            oldfile=open('/var/www/Connections_Seen.json','r')
                            jcontents = oldfile.readlines()
                            oldfile.close()
                            jcontents.insert(4, '     {\n')
                            jcontents.insert(5, '        "type": "Feature",\n')
                            jcontents.insert(6, '        "geometry": {\n')
                            jcontents.insert(7, '           "type": "Point",\n')
                            jcontents.insert(8, '           "coordinates": [' + srclong + ',' + srclat + ']' + '\n')
                            jcontents.insert(9, '           },' + '\n')
                            jcontents.insert(10, '        "properties": {\n')
                            jcontents.insert(11, '        "description":  "' +  src + ':' + srcport + ' to ' + dst + ':' + dstport + ', '  + country + ', ' + state + ', ' + city + ', ' + zip + '",\n')
                            jcontents.insert(12, '        "color": "' + color + '"\n')
                            jcontents.insert(13, '        }\n')
                            jcontents.insert(14, '     },\n')
                            jcontents.insert(15, '\n')
                            jcontents.insert(16, '     {\n')
                            jcontents.insert(17, '        "type": "Feature",\n')
                            jcontents.insert(18, '        "geometry": {\n')
                            jcontents.insert(19, '           "type": "LineString",\n')
                            jcontents.insert(20, '           "coordinates": [[' + srclong + ',' + srclat + '], [' + homelong + ',' + homelat + ']]\n')
                            jcontents.insert(21, '        },' + '\n')
                            jcontents.insert(22, '        "properties": {\n')
                            jcontents.insert(23, '        "description":  "' +  src + ':' + srcport + ' to ' + dst + ':' + dstport + ', '  + country + ', ' + state + ', ' + city + ', ' + zip + '",\n')
                            jcontents.insert(24, '        "color": "' + color + '"\n')
                            jcontents.insert(25, '         }' + '\n')
                            jcontents.insert(26, '      }' + ', \n')
                            jcontents.insert(27, '\n')
                            newfile=open('/var/www/tmpfile', 'w')
                            jcontents = "".join(jcontents)
                            newfile.write(jcontents)
                            newfile.close()
                            #newlines[24] = '                "description": ' + str(cid) + ', ' + str(ptime) + ', ' + src + ':' + srcport + ', ' dst + ':' + dstport + ', '  + country + ', ' + state + ', ' + city + ', ' + zip + '\n'
                            os.rename('/var/www/tmpfile', '/var/www/Connections_Seen.json')
                        #done writing to the json file, now to update the right.html:
                        oldfile=open('/var/www/right.html','r')
                        rcontents = oldfile.readlines()
                        oldfile.close()
                        rcontents.insert(21, '<font color="' + color + '">' + src + ':' + srcport + ' to ' + dst + ':' + dstport + ',' + country + ' ' + state + ' '  + city + '</br>' + '\n')
                        newfile=open('/var/www/tmpfile2', 'w')
                        rcontents = "".join(rcontents)
                        newfile.write(rcontents)
                        newfile.close()
                        os.rename('/var/www/tmpfile2', '/var/www/right.html')
                        startfile = "chown -R www-data /var/www/"
                        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        startfile = "chgrp -R www-data /var/www"   #need to change privs to www-data so that the web user can clear the screen
                        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        ps.wait()
                            #print "CID: " + str(cid) + " Time: " + str(ptime) + " Src: " + src + ":" + srcport + " Dst: " + dst + ":" + dstport + " Proto: " + prototype + " SrcLat: " + srclat + " SrcLong: " + srclong + " DstLat: " + dstlat + " DstLong: " + dstlong + " " + country + " " + state + " " + city + " " + zip
                            #print prototype + " packet from: " + src + " srcport: " + srcport + " at: " + otherlat + " " + otherlong + " at " + country + " "  + state + " " + city + " " + zip + " to " + dst + " dstport:  " + dstport 
                    #elif not (dst.startswith("209.85.") or dst.startswith("172.217.") or dst.startswith("209.85.202.") or dst.startswith("64.233.") or dst.startswith("8.8.8.") or dst.startswith("216.58.") or dst.startswith("173.194.") or dst.startswith("74.125.") or (int(dst.split(".")[0]) > 223 and int(dst.split(".")[0]) < 240) or dst.startswith("0.") or dst.startswith("255.") or dst.startswith("10.") or dst.startswith("192.168.") or dst.startswith("172.16.")):
                    elif not (eval(chkdst)):
                        getcoords = "/usr/bin/geoiplookup -f /usr/local/share/GeoIP/GeoLiteCity.dat " + dst
                        #print "running this: " + getcoords
                        global cid 
                        cid = cid + 1
                        ptime = time.strftime("%y.%m.%d.%H.%M.%S")
                        ps = subprocess.Popen(getcoords, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        out, err = ps.communicate()
                        country = out.split(":")[1]
                        country = country.split(",")[0]
                        try:
                            state = out.split(",")[2]             #I've errored out on this line a lot.... error checking is needed
                        except IndexError:
                        	state = "NA"
                        try:
                            city = out.split(",")[3]
                        except IndexError:
                        	city = "NA"
                        try:
                            zip = out.split(",")[4]
                        except IndexError:
                        	zip = "NA"
                        srclat = homelat
                        srclong = homelong
                        try:
                        	dstlat = str(out.split(",")[6])
                        except IndexError:
                        	dstlat = "NA"
                        try:
                        	dstlong = str(out.split(",")[7])
                        except IndexError:
                        	dstlong = "NA"
                        dstlat = dstlat[1:]
                        dstlong = dstlong[1:] 
                        country = country[1:]
                        if country[0:20] == "IP Address not found":  # Maxmind doesn't know where this is
                            country = "IP Unknown"
                            state = " NA"
                            city = " NA"
                            zip = " NA"
                        state = state[1:]
                        state = filter(lambda x: x in string.printable, state)
                        city = city[1:]
                        city = filter(lambda x: x in string.printable, city)
                        zip = zip[1:]
                        if len(zip) < 2:
                            zip = "N/A"
                        #print "From Home country is: " + country + " state is: " + state + " city is: " + city + " zip is: " + zip + " srclat is: " + srclat + "srclong is: " + srclong + " dstlat is: " + dstlat + "dstlong is: " + dstlong
                        stringtoappend = str(cid) + ",20" + str(ptime) + "," + src + ":" + srcport + "," + dst + ":" + dstport + "," + prototype + "," + srclat + "," + srclong + "," + dstlat + "," + dstlong + "," + country + "," + state + "," + city + "," + zip + "\n"
                        print stringtoappend
                        if prototype == "TCP":
                            color = 'red'
                        elif prototype == "ICMP":
                            color = 'green'
                        elif prototype == "UDP":
                            color = 'blue'
                        with open(filename, "a") as myfile:
                            myfile.write(stringtoappend)
                        #update JSON file if the point is unique
                        if not (dstlat in PointList and dstlong in PointList and PointList.index(dstlat) + 1 == PointList.index(dstlong) or (country == "IP Unknown") or (not(is_number(dstlat)) or (not(is_number(dstlong))))):
                            #print "Point: " + dstlat + ", " + dstlong + " is NOT the JSON file.  Adding it"
                            PointList.append(dstlat)
                            PointList.append(dstlong)
                            global numbpreviouslines 
                            numbpreviouslines= numbpreviouslines + 25 # 29 lines below, plus I write over 0-3
                            oldfile=open('/var/www/Connections_Seen.json','r')
                            jcontents = oldfile.readlines()
                            oldfile.close()
                            jcontents.insert(4, '     {\n')
                            jcontents.insert(5, '        "type": "Feature",\n')
                            jcontents.insert(6, '        "geometry": {\n')
                            jcontents.insert(7, '           "type": "Point",\n')
                            jcontents.insert(8, '           "coordinates": [' + dstlong + ',' + dstlat + ']' + '\n')
                            jcontents.insert(9, '           },' + '\n')
                            jcontents.insert(10, '        "properties": {\n')
                            jcontents.insert(11, '        "description":  "' +  src + ':' + srcport + ' to ' + dst + ':' + dstport + ', '  + country + ', ' + state + ', ' + city + ', ' + zip + '",\n')
                            jcontents.insert(12, '        "color": "' + color + '"\n')
                            jcontents.insert(13, '        }\n')
                            jcontents.insert(14, '     },\n')
                            jcontents.insert(15, '\n')
                            jcontents.insert(16, '     {\n')
                            jcontents.insert(17, '        "type": "Feature",\n')
                            jcontents.insert(18, '        "geometry": {\n')
                            jcontents.insert(19, '           "type": "LineString",\n')
                            jcontents.insert(20, '           "coordinates": [[' + homelong + ',' + homelat + '], [' + dstlong + ',' + dstlat + ']]\n')
                            jcontents.insert(21, '           },' + '\n')
                            jcontents.insert(22, '        "properties": {\n')
                            jcontents.insert(23, '           "description":  "' +  src + ':' + srcport + ' to ' + dst + ':' + dstport + ', '  + country + ', ' + state + ', ' + city + ', ' + zip + '",\n')
                            jcontents.insert(24, '           "color": "' + color + '"\n')
                            jcontents.insert(25, '           }' + '\n')
                            jcontents.insert(26, '        }' + ', \n')
                            jcontents.insert(27, '\n')
                            newfile=open('/var/www/tmpfile', 'w')
                            jcontents = "".join(jcontents)
                            newfile.write(jcontents)
                            newfile.close()  
                            #newlines[24] = '                "description": ' + str(cid) + ', ' + str(ptime) + ', ' + src + ':' + srcport + ', ' dst + ':' + dstport + ', '  + country + ', ' + state + ', ' + city + ', ' + zip + '\n'
                            os.rename('/var/www/tmpfile', '/var/www/Connections_Seen.json')
                            startfile = "chown -R www-data /var/www/"
                            ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            startfile = "chgrp -R www-data /var/www"   #need to change privs to www-data so that the web user can clear the screen
                            ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            ps.wait()
                        #done writing to the json file, now to update the right.html:
                        oldfile=open('/var/www/right.html','r')
                        rcontents = oldfile.readlines()
                        oldfile.close()
                        rcontents.insert(21, '<font color="' + color + '">' + src + ':' + srcport + ' to ' + dst + ':' + dstport + ',' + country + ' ' + state + ' ' + city + '</br>' + '\n')
                        newfile=open('/var/www/tmpfile2', 'w')
                        rcontents = "".join(rcontents)
                        newfile.write(rcontents)
                        newfile.close()
                        os.rename('/var/www/tmpfile2', '/var/www/right.html')
                        startfile = "chown -R www-data /var/www"
                        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        startfile = "chgrp -R www-data /var/www"
                        ps = subprocess.Popen(startfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        ps.wait()
                        #print prototype + " packet from " + src + " srcport: " + srcport + " to " + dst + " dstport: " + dstport + " at: " + lat + " " + long + " at " + country + " "  + state + " " + city + " " + zip
                    #if not ((src.startswith("10.") or src.startswith("192.168.") or src.startswith("172.16.")) and (dst.startswith("10.") or dst.startswith("192.168.") or dst.startswith("172.16."))):
                        #print 'Src: ' + src + ' Dst: ' + dst
if __name__ == "__main__":
  main(sys.argv)
