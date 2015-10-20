__author__ = 'Sam Hiatt'
from pymongo import MongoClient
import re
import numpy as np
from datetime import datetime
from pandas import DataFrame
from GTOPO30 import getElevationProfile
from LatLon import LatLon

FEET_PER_METER = 3.28084
ELEV_THRESHOLD = 200/FEET_PER_METER
TOPO_THRESHOLD = 500/FEET_PER_METER
DISTANCE_THRESHOLD = 15000

client = MongoClient('localhost',27017)
db = client['stationdata']
stations=db['stations']
stations.ensure_index([("loc","2dsphere")])

stationsQuery = stations.find({
        "_id":re.compile('^KCASANFR')
    }).limit(5)
print "%i stations"%stationsQuery.count()
for station in stationsQuery:
    # Get nearby stations
    t0neighborQuery = datetime.now()
    neighborQuery = stations.find({
            "_id":{"$ne":station['_id']},
            "loc":{"$near":{"$geometry":station['loc'],
               "$maxDistance":DISTANCE_THRESHOLD}
              }
        }).limit(5)
    t0NeighborLoop = datetime.now()
    dt = datetime.now() - t0neighborQuery
    print("Neighbor query: %.6fs"%dt.total_seconds())
    if neighborQuery.count()==np.nan:
        print "Station %s has no nearby stations."%station['_id']
    else:
        print "%s's %i neighbors:"%(station['_id'],neighborQuery.count())
        c0 = station['loc']['coordinates']
        stationLoc = LatLon(c0[1],c0[0])
        neighborCount = 0
        for neighbor in neighborQuery:
            neighborCount+=1
            c1 = neighbor['loc']['coordinates']
            elevProfile = DataFrame(getElevationProfile(c0[0],c0[1],c1[0],c1[1]),
                                    columns=('lon','lat','elev'))
            elevs=elevProfile['elev']
            elevs[elevs==-9999]=0  # set no-data to 0
            #print (elevProfile)
            relativePeakHeight = elevs.max() \
                - np.max([elevs[0],elevs[len(elevProfile)-1]])
            neighborLoc = LatLon(c1[1],c1[0])
            dist = stationLoc.distance(neighborLoc)
            # TODO:
            #  - check relativePeakHeight against threshold
            #  - check proximity to water

            print(neighbor['_id'], elevs.max(),relativePeakHeight,dist)
    print("StationLoop: %i stations, %.6fs"%(neighborCount,(datetime.now()-t0NeighborLoop).total_seconds()))