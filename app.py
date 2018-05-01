# coding: utf-8

from flask import Flask, render_template, Response
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map, icons
import configparser

app = Flask(__name__, template_folder="templates")

# you can set key as config
app.config['GOOGLEMAPS_KEY'] = YOURKEY
GoogleMaps(app, key=YOURKEY)

config = configparser.ConfigParser()
config.read('TapAndMap.conf')


@app.route("/")
def mapview():
    geodesic_line = {
        'stroke_color': '#0AB0DE',
        'stroke_opacity': 1.0,
        'stroke_weight': 3,
        'geodesic': True,
    }

    path = [(float(config['all']['HomeLat']),
             float(config['all']['HomeLong'])),
            (37.4300, -122.1400)]

    tap_and_map = Map(
        identifier="tapandmap",
        varname="tapandmap",
        lat=config['all']['HomeLat'],
        lng=config['all']['HomeLong'],
        style="height:100vh;width:70vw;margin:0;float:left;",
        zoom=config['all']['ZoomLevel'],
        fit_markers_to_bounds=True,
        polylines=[geodesic_line, path],
        markers=[
            {
                'icon': icons.alpha.A,
                'lat': config['all']['HomeLat'],
                'lng': config['all']['HomeLong'],
                'infobox': "This is your TapAndMap server.  IP: " +
                config['all']['TapAndMapIP']
            },
            {
                'icon': icons.dots.blue,
                'lat': 37.4300,
                'lng': -122.1400,
                'infobox': "Hello I am <b style='color:blue;'>BLUE</b>!",
            },
        ],
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
