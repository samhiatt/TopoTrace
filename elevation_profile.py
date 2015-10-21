import argparse, json
from GTOPO30 import getElevationProfile
from LatLon import LatLon

parser = argparse.ArgumentParser(description='Get elevation profile for a line between two points.')
parser.add_argument('--lat0', dest='lat0', action='store', type=float, default = -999)
parser.add_argument('--lon0', dest='lon0', action='store', type=float, default = -999)
parser.add_argument('--lat1', dest='lat1', action='store', type=float, default = -999)
parser.add_argument('--lon1', dest='lon1', action='store', type=float, default = -999)
args=parser.parse_args()

p0 = LatLon(args.lat0,args.lon0)
p1 = LatLon(args.lat1,args.lon1)
elevProfile = getElevationProfile(p0,p1)
elevProfile = [{"lon":x,"lat":y,"elev":float(z)} for x,y,z in elevProfile]
print json.dumps(elevProfile)