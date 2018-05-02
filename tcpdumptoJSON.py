# coding: utf-8
import json
import time
from scapy.all import sniff


def main():
    def custom_action():
        def jsonwritter(packet):
            timestr = time.strftime("%Y%m%d-%H%M%S")
            with open('packetInfo ' + timestr + '.json', 'a') as json_file:
                packet_info = [{'proto': packet[0][1].proto,
                                'src': packet[0][1].src,
                                'dst': packet[0][1].dst}]
                json.dump(packet_info, json_file)
        return jsonwritter

    sniff(filter="ip or icmp", store=False, prn=custom_action())


if __name__ == "__main__":
    main()
