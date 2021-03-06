import SocketServer
import BaseHTTPServer
import json
from urlparse import urlparse, parse_qs
from GTOPO30 import getElevation, getElevationProfile
from find_station_neighbors import getFilteredNeighbors, stations

PORT = 9000

FEET_PER_METER = 3.28084

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        """Respond to a GET request."""
        req = urlparse(s.path)
        if req.path.startswith('/index.html'):
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
            s.wfile.write(open('public/index.html').read())
        elif req.path.startswith('/elevationProfile'):
            query = parse_qs(req.query)
            try:
                elevProfile = getElevationProfile(
                    float(query['lon0'][0]),
                    float(query['lat0'][0]),
                    float(query['lon1'][0]),
                    float(query['lat1'][0]))
            except:
                s.send_response(500)
                return
            max = -9999
            min = 9000000
            for x,y,z in elevProfile:
                if z > max: max = z
                if z > -999 and z < min: min = z
            elevProfile = [{"lon":x,"lat":y,"elev":float(z)} for x,y,z in elevProfile]
            resp = {
                "maxElevation": float(max),
                "minElevation": float(min),
                "units": 'meters',
                "points": elevProfile
            }
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            s.wfile.write(json.dumps(resp))
        elif req.path.startswith('/getElevation'):
            query = parse_qs(req.query)
            try:
                lon,lat=(query['lon'][0],query['lat'][0])
                elev = getElevation(lon,lat)
            except:
                s.send_response(500)
                return
            resp = {
                "elev": float(elev),
                "lat": float(lat),
                "lon": float(lon),
                "units": 'meters'
            }
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            s.wfile.write(json.dumps(resp))
        elif req.path.startswith('/getFilteredNeighbors'):
            query = parse_qs(req.query)
            try:
                stationId = query['stationId'][0]
                topoThresh = query['topoThresh']
                if len(topoThresh)>0: topoThresh = float(topoThresh[0])/FEET_PER_METER
                elevThresh = query['elevThresh']
                if len(elevThresh)>0: elevThresh = float(elevThresh[0])/FEET_PER_METER
                station = stations.find_one({
                    "_id":stationId
                },{
                    "loc":1
                })
            except:
                s.send_response(500)
                return
            if station:
                filteredNeighbors, neighbors = getFilteredNeighbors(station,topoThresh=topoThresh,elevThresh=elevThresh)
                resp={"station":station,
                      "filteredNeighbors":filteredNeighbors,
                      "neighbors":neighbors
                      }
            else: resp={}
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            s.wfile.write(json.dumps(resp))
        else:
            s.send_response(500)

httpd = SocketServer.TCPServer(("", PORT), MyHandler)

print "serving at port", PORT
httpd.serve_forever()