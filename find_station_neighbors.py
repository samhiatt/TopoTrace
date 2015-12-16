__author__ = 'Sam Hiatt'
from pymongo import MongoClient
import re
import numpy as np
from datetime import datetime
from GTOPO30 import getElevationProfile
from LatLon import LatLon

FEET_PER_METER = 3.28084
ELEV_THRESHOLD = 200/FEET_PER_METER
TOPO_THRESHOLD = 400/FEET_PER_METER
DISTANCE_THRESHOLD = 15000

client = MongoClient('localhost',27017)
db = client['stationdata']
stations=db['stations']
stations.ensure_index([("loc","2dsphere")])


def getFilteredNeighbors(station,topoThresh=TOPO_THRESHOLD,elevThresh=ELEV_THRESHOLD):
    # Get nearby stations
    # t0neighborQuery = datetime.now()
    neighborQuery = stations.find({
            "_id":{"$ne":station['_id']},
            "loc":{"$near":{"$geometry":station['loc'],
               "$maxDistance":DISTANCE_THRESHOLD}
              }
        },
        {
            "loc":1
        })#.limit(5)
    t0NeighborLoop = datetime.now()
    # dt = datetime.now() - t0neighborQuery
    # print("Neighbor query: %.6fs"%dt.total_seconds())
    neighbors = []
    filteredNeighbors=[]
    if neighborQuery.count()==np.nan:
        print "Station %s has no nearby stations."%station['_id']
    else:
        # print "%s's %i nearby stations:"%(station['_id'],neighborQuery.count())
        c0 = station['loc']['coordinates']
        stationLoc = LatLon(c0[1],c0[0])
        neighborCount = 0
        for neighbor in neighborQuery:
            neighbors.append(neighbor)
            neighborCount+=1
            c1 = neighbor['loc']['coordinates']
            neighborLoc = LatLon(c1[1],c1[0])
            # t0topoQuery = datetime.now()
            elevProfile = np.array(getElevationProfile(stationLoc.lon.decimal_degree,
                                                       stationLoc.lat.decimal_degree,
                                                       neighborLoc.lon.decimal_degree,
                                                       neighborLoc.lat.decimal_degree))
            elevs=elevProfile[:,2]
            #print (elevProfile)
            relativePeakHeight = elevs.max() \
                - np.max([elevs[0],elevs[-1]])
            neighbor['distance'] = stationLoc.distance(neighborLoc)
            # print(neighbor['_id'], elevs.max(),relativePeakHeight,dist)
            elevDiff = abs(elevs[0]-elevs[-1])
            if relativePeakHeight<topoThresh and elevDiff < elevThresh:
                filteredNeighbors.append(neighbor)
        #print("StationLoop: %i stations, %.6fs"%(neighborCount,(datetime.now()-t0NeighborLoop).total_seconds()))
        return filteredNeighbors, neighbors

if __name__=='__main__':
    stationsQuery = stations.find({
            "_id":re.compile('^KCASANFR')
        })
    print "%i stations"%stationsQuery.count()
    cnt=0
    t0=datetime.now()
    for station in stationsQuery:
        cnt+=1
        filteredNeighbors = [s['_id'] for s in getFilteredNeighbors(station)[0]]
        print("Done with station %s, %i of %i"%(station['_id'],cnt,stationsQuery.count()))
        stations.update({"_id":station['_id']},{"$set":{"filteredNeighbors":filteredNeighbors}},upsert=True)
        print('')
    print("Done. %is"%(datetime.now()-t0).total_seconds())
