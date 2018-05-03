# coding: utf-8
import os
import json
from scapy.all import sniff


def main():
    def custom_action():
        increment = 0
        if os.path.isfile('packetInfo' + str(increment) + '.json'):
            fileinfo = os.stat('packetInfo' + str(increment) + '.json')
            if fileinfo.st_size > 5120:  # need to test if this works
                increment += 1
        filename = 'packetInfo' + str(increment) + '.json'

        def jsonwritter(packet):
            with open(filename, 'a') as json_file:
                packet_info = [{'proto': packet[0][1].proto,
                                'src': packet[0][1].src,
                                'dst': packet[0][1].dst}]
                json.dump(packet_info, json_file)
        return jsonwritter

    sniff(filter="ip or icmp", store=False, prn=custom_action())


if __name__ == "__main__":
    main()
