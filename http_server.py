import SocketServer
import BaseHTTPServer
import json
from urlparse import urlparse, parse_qs
from GTOPO30 import getElevation, getElevationProfile

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
        else:
            query = parse_qs(req.query)
            try:
                x0,y0,x1,y1=(query['lon0'][0],query['lat0'][0],query['lon1'][0],query['lat1'][0])
                elevProfile = getElevationProfile(x0,y0,x1,y1)
            except:
                s.send_response(500)
                return
            resp=[]
            max = -9999
            min = 9000000
            for x,y,z in elevProfile:
                resp.append('{"lat":%s,"lon":%s,"elev":%s}'%(y,x,z))
                if z > max: max = z
                if z > -999 and z < min: min = z
            # resp = ['{"lat":%s,"lon":%s,"elev":%s}'%(y,x,z) for x, y, z in elevProfile ]
            s.send_response(200)
            s.send_header("Content-type", "application/json")
            s.end_headers()
            s.wfile.write('{"maxElevation": %i, "minElevation": %i, '%(max,min)+'"points": ['+','.join(resp)+']}')

httpd = SocketServer.TCPServer(("", PORT), MyHandler)

print "serving at port", PORT
httpd.serve_forever()