# coding: utf-8

from flask import Flask, render_template, Response
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map, icons
import configparser
import redis

app = Flask(__name__, template_folder="templates")

# you can set key as config
app.config['GOOGLEMAPS_KEY'] =
GoogleMaps(app, key="")

config = configparser.ConfigParser()
config.read('TapAndMap.conf')


@app.route("/")
def mapview():
    geodesic_line = {
        'stroke_color': '#00FF00',
        'stroke_opacity': 1.0,
        'stroke_weight': 3,
        'geodesic': True,
        'path': [(float(config['all']['HomeLat']),
                  float(config['all']['HomeLong'])),
                 (37.4300, -122.1400)
                 ]
    }

    geodesic_line2 = {
        'stroke_color': '#0000FF',
        'stroke_opacity': 1.0,
        'stroke_weight': 3,
        'geodesic': True,
        'path': [(float(config['all']['HomeLat']),
                  float(config['all']['HomeLong'])),
                 (60.4300, -80.1400)
                 ]
    }

    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    markersL = [{'icon': icons.alpha.A,
                 'lat': config['all']['HomeLat'],
                 'lng': config['all']['HomeLong'],
                 'infobox': "This is your TapAndMap server.  IP: " +
                 config['all']['TapAndMapIP']}]
    polyL = [geodesic_line, geodesic_line2]

    for key in r.scan_iter("*"):
        if key.split(b':')[1] == b'1':  # ICMP
            icon = icons.dots.blue
        elif key.split(b':')[1] == b'6':  # TCP
            icon = icons.dots.yellow
        elif key.split(b':')[1] == b'17':  # UDP
            icon = icons.dots.green
        try:
            markersL.append({'icon': icon,
                             'lat': r.get(key).split(b'x')[0].decode("UTF-8"),
                             'lng': r.get(key).split(b'x')[1].decode("UTF-8"),
                             'infobox': 'IP:' +
                             key.split(b':')[0].decode("UTF-8"),
                             })
            polyL2 = {'stroke_color': '#0000FF',
                      'stroke_opacity': 1.0,
                      'stroke_weight': 3,
                      'geodesic': True,
                      'path': [(float(config['all']['HomeLat']),
                                float(config['all']['HomeLong'])),
                               (r.get(key).split(b'x')[0].decode("UTF-8"),
                                r.get(key).split(b'x')[1].decode("UTF-8"))
                               ]
                      }

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
        polylines=polyL,
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
