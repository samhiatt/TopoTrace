import SocketServer
import BaseHTTPServer
import json
from urlparse import urlparse, parse_qs
from GTOPO30 import getElevation, getElevationProfile
from find_station_neighbors import getFilteredNeighbors, stations

PORT = 9000

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
                x0,y0,x1,y1=(query['lon0'][0],query['lat0'][0],query['lon1'][0],query['lat1'][0])
                elevProfile = getElevationProfile(x0,y0,x1,y1)
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
                station = stations.find_one({"_id":stationId})
            except:
                s.send_response(500)
                return
            resp=getFilteredNeighbors(station)
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            s.wfile.write(json.dumps(resp))
        else:
            s.send_response(500)

httpd = SocketServer.TCPServer(("", PORT), MyHandler)

print "serving at port", PORT
httpd.serve_forever()