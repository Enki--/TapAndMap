# coding: utf-8
import redis
import ipaddress
import geoip2.database
from scapy.all import sniff


def main():
    def custom_action(redisObject, reader):
        def redis_writter(packet):
            if not ipaddress.ip_address(packet[0][1].src).is_private:
                redisKey = str(packet[0][1].src) + ":" + str(
                    packet[0][1].proto)
                if not redisObject.exists(redisKey):
                    try:
                        IPGeo = reader.city(packet[0][1].src)
                        redisValue = str(IPGeo.location.latitude) + "x" + str(
                            IPGeo.location.longitude)
                    except geoip2.errors.AddressNotFoundError:
                        redisValue = "N/A"
                    redisObject.set(redisKey, redisValue)
                else:
                    pass
            elif not ipaddress.ip_address(packet[0][1].dst).is_private:
                redisKey = str(packet[0][1].dst) + ":" + str(
                    packet[0][1].proto)
                if not redisObject.exists(redisKey):
                    try:
                        IPGeo = reader.city(packet[0][1].dst)
                        redisValue = str(IPGeo.location.latitude) + "x" + str(
                            IPGeo.location.longitude)
                    except geoip2.errors.AddressNotFoundError:
                        redisValue = "N/A"
                    redisObject.set(redisKey, redisValue)
                else:
                    pass
        return redis_writter
    if __name__ == "__main__":
        redisDB = redis.StrictRedis(host="localhost", port=6379, db=0)
        reader = geoip2.database.Reader('GeoLite2-City.mmdb')
    sniff(filter="ip or icmp", store=False, prn=custom_action(redisDB, reader))


if __name__ == "__main__":
    main()
