__author__ = 'Sam Hiatt'

from pymongo import MongoClient
import re
import numpy as np
from pandas import DataFrame
from GTOPO30 import getElevationProfile
from LatLon import LatLon


client = MongoClient('localhost',27017)

db = client['stationdata']

stations=db['stations']

stations.ensure_index([("loc","2dsphere")])


for station in stations.find({
        "_id":re.compile('^KCASANFR')
    }).limit(5):
    # Get nearby stations
    neighborQuery = stations.find({
            "_id":{"$ne":station['_id']},
            "loc":{"$near":{"$geometry":station['loc'],
               "$maxDistance":3000}
              }
        }).limit(5)
    if neighborQuery.count()==np.nan:
        print "Station %s has no neighbors."%station['_id']
    else:
        print "%s's neighbors:"%station['_id']
        c0 = station['loc']['coordinates']
        stationLoc = LatLon(c0[1],c0[0])
        for neighbor in neighborQuery:
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