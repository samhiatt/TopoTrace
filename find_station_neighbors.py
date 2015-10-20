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
TOPO_THRESHOLD = 400/FEET_PER_METER
DISTANCE_THRESHOLD = 15000
WATER_DISTANCE_THRESHOLD = 2000/FEET_PER_METER

client = MongoClient('localhost',27017)
db = client['stationdata']
stations=db['stations']
stations.ensure_index([("loc","2dsphere")])

topodb = client['topo']
water = topodb['topo.water']


def getFilteredNeighbors(station,topoThresh=TOPO_THRESHOLD):
    # t0waterQuery = datetime.now()
    waterQuery = water.find({
        "geometry":{"$near":{
            "$geometry": station['loc'],
            "$maxDistance": WATER_DISTANCE_THRESHOLD}
        }})
    stationNearWater = waterQuery.count()>0
    # print("%s, %i bodies of water, found in %.6fs"%(station['_id'],waterQuery.count(),(datetime.now()-t0waterQuery).total_seconds()))
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
            # t0topoQuery = datetime.now()
            elevProfile = DataFrame(getElevationProfile(c0[0],c0[1],c1[0],c1[1]),
                                    columns=('lon','lat','elev'))
            elevs=elevProfile['elev']
            elevProfile.loc[elevs==-9999,'elev']=0  # set no-data to 0
            #print (elevProfile)
            relativePeakHeight = elevs.max() \
                - np.max([elevs[0],elevs[len(elevProfile)-1]])
            neighborLoc = LatLon(c1[1],c1[0])
            dist = stationLoc.distance(neighborLoc)
            # print(neighbor['_id'], elevs.max(),relativePeakHeight,dist)
            hillNeighbors = True
            waterNeighbors = False
            if relativePeakHeight>topoThresh:
                hillNeighbors=False
            # TODO: Check elev difference between the two stations (should be <= 200ft)
            # str = " "
            # if hillNeighbors: str=" not"
            # print("%s is%s blocked by hill. %.6fs"%(neighbor['_id'],str,(datetime.now()-t0topoQuery).total_seconds()))
            # t0waterQuery = datetime.now()
            waterQuery = water.find({
                "geometry":{"$near":{
                    "$geometry": neighbor['loc'],
                    "$maxDistance": WATER_DISTANCE_THRESHOLD}
                }})
            # print ("%s has %i bodies of water nearby. %.6fs"%(
            #     neighbor['_id'],
            #     waterQuery.count(),
            #     (datetime.now()-t0waterQuery).total_seconds()
            # ))
            neighborNearWater = waterQuery.count()>0
            if (stationNearWater and neighborNearWater) or (not stationNearWater and not neighborNearWater):
                waterNeighbors = True
            # if (waterNeighbors and hillNeighbors): str = " "
            # else: str = " not"
            # print("%s and %s are%s neighbors"%(neighbor['_id'],station['_id'],str))
            if (waterNeighbors and hillNeighbors): filteredNeighbors.append(neighbor)
        print("StationLoop: %i stations, %.6fs"%(neighborCount,(datetime.now()-t0NeighborLoop).total_seconds()))
        return filteredNeighbors, neighbors

if __name__=='__main__':
    stationsQuery = stations.find({
            "_id":re.compile('^KCAMODES')
        })
    print "%i stations"%stationsQuery.count()
    cnt=0
    t0=datetime.now()
    for station in stationsQuery:
        cnt+=1
        filteredNeighbors = [s['_id'] for s in getFilteredNeighbors(station)[0]]
        print("Done with station %s, %i of %i"%(station['_id'],cnt,stationsQuery.count()))
        stations.update({"_id":station['_id']},{"$set":{"filteredNeighbors":filteredNeighbors}})
        print('\n')
    print("Done. %is"%(datetime.now()-t0).total_seconds())
