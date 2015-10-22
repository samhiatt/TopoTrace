from pymongo import MongoClient
import json

client = MongoClient('localhost',27017)

db = client['stationdata']

stations=db['stations']

with open("stations.json") as infile:
    data = json.loads(infile.read())

for i, station in enumerate(data):
    stations.update({
        "_id":station['_id']
    },{
        "$set":{"loc":station['loc']}
    },upsert=True)
    if i%10000==0: print("Inserted %i stations"%i)

stations.ensure_index([("loc","2dsphere")])
print "Done."