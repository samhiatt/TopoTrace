import argparse, json
from GTOPO30 import getElevationProfile

parser = argparse.ArgumentParser(description='Get elevation profile for a line between two points.')
parser.add_argument('--lat0', dest='lat0', action='store', type=float, default = -999)
parser.add_argument('--lon0', dest='lon0', action='store', type=float, default = -999)
parser.add_argument('--lat1', dest='lat1', action='store', type=float, default = -999)
parser.add_argument('--lon1', dest='lon1', action='store', type=float, default = -999)
args=parser.parse_args()

elevProfile = getElevationProfile(args.lon0,args.lat0,args.lon1,args.lat1)
elevProfile = [{"lon":x,"lat":y,"elev":float(z)} for x,y,z in elevProfile]
print json.dumps(elevProfile)