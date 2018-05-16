# coding: utf-8
#!/usr/bin/env python3

import redis
import configparser
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map, icons
from flask import Flask, render_template, Response


app = Flask(__name__, template_folder="templates")

# you can set key as config
app.config['GOOGLEMAPS_KEY'] = "Add Key"
GoogleMaps(app, key="Add Key")

config = configparser.ConfigParser()
config.read('TapAndMap.conf')


@app.route("/")
def mapview():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    markersL = [{'icon': icons.alpha.A,
                 'lat': config['all']['HomeLat'],
                 'lng': config['all']['HomeLong'],
                 'infobox': "This is your TapAndMap server.  IP: " +
                 config['all']['TapAndMapIP']}]
    geolines = []
    for key in r.scan_iter("*"):
        if key.split(b':')[1] == b'1':  # ICMP
            icon = icons.dots.blue
            line = '#0000FF'
        elif key.split(b':')[1] == b'6':  # TCP
            icon = icons.dots.yellow
            line = '#FFFF00'
        elif key.split(b':')[1] == b'17':  # UDP
            icon = icons.dots.green
            line = '#00FF00'
        try:
            markersL.append({'icon': icon,
                             'lat': r.get(key).split(b'x')[0].decode("UTF-8"),
                             'lng': r.get(key).split(b'x')[1].decode("UTF-8"),
                             'infobox': 'IP:' +
                             key.split(b':')[0].decode("UTF-8"),
                             })

            pathList = [{'lat': float(config['all']['HomeLat']),
                         'lng': float(config['all']['HomeLong'])},
                        {'lat': float(
                                r.get(key).split(b'x')[0].decode("UTF-8")),
                         'lng': float(
                                r.get(key).split(b'x')[1].decode("UTF-8"))}]

            geolines.append({'stroke_color': line,
                             'stroke_opacity': 1.0,
                             'stroke_weight': 3,
                             'geodesic': True,
                             'path': pathList
                             }
                            )
        except IndexError:
            pass

    tap_and_map = Map(
        identifier="tapandmap",
        varname="tapandmap",
        lat=config['all']['HomeLat'],
        lng=config['all']['HomeLong'],
        style="height:100vh;width:70vw;margin:0;float:left;",
        zoom=config['all']['ZoomLevel'],
        fit_markers_to_bounds=True,
        polylines=geolines,
        markers=markersL
    )

    return render_template(
        'index.html',
        tap_and_map=tap_and_map,
    )


@app.errorhandler(404)
def not_found(exc):
    return Response('<h1>There is only one page, and this is not it'), 404


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
