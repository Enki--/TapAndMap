# coding: utf-8
import json
from scapy.all import sniff


def main():
    def custom_action(w_file):
        def jsonwritter(packet):
            packet_info = [{'proto': packet[0][1].proto,
                            'src': packet[0][1].src,
                            'dst': packet[0][1].dst}]
            json.dump(packet_info, w_file)
        return jsonwritter

    with open('packetInfo.json', 'w') as json_file:
        sniff(filter="ip or icmp", prn=custom_action(json_file))


if __name__ == "__main__":
    main()
