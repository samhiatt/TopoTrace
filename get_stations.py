from pymongo import MongoClient
import json

client = MongoClient('localhost',27099)
db = client['stationdata']
stations=db['stations']

stationsCursor = stations.find({
                                    "loc":{"$exists":1},
                                    "updated":{"$exists":1}
                                },{
                                    "loc":1
                                })
print ("%i stations."%stationsCursor.count())
res = []
for station in stationsCursor:
    res.append(station)

with open("stations.json",'w') as outfile:
    outfile.write(json.dumps(res))

print "Done."