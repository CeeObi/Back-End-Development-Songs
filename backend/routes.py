from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def health():
    return {"status":"OK"}


@app.route("/count")
def count():     
    count = db.songs.count_documents({})
    return {"count":count}, 200


@app.route("/song")
def songs():     
    allsong = db.songs.find({})    
    song_list=json_util.dumps(allsong)
    song_list = json.loads(song_list)
    return {"songs":song_list}, 200



@app.route("/song/<id>")
def get_song_by_id(id):
    id=int(id)
    song = db.songs.find_one({"id": id})
    
    if not song:
        return {"message":"song with id not found"},404
    else:
        song = json_util.dumps(song)        
        return song,200


@app.route("/song", methods=["POST"])
def create_song():
    song_ext = request.get_data()
    song_ext = json_util.loads(song_ext)
    db_songs = db.songs.find({})
    for each_song in db_songs:        
        if each_song["id"] == song_ext["id"]:
            return {"Message":f"song with id {song_ext['id']} already present"}        
    add_song = db.songs.insert_one(song_ext)    
    return {"inserted id":{"$oid":f"{add_song.inserted_id}"}}


@app.route("/song/<id>", methods=["PUT"])
def update_song(id):
    id=int(id)
    song_ext = request.get_data()
    song_ext = json_util.loads(song_ext)
    song = db.songs.find_one({"id": id})    
    
    if not song:
        return {"message":"song not found"},404
    else:   
        if song["lyrics"] == song_ext["lyrics"]:
            return {"message":"song found, but nothing updated"}
        else:
            song = json_util.dumps(song)        
            update = db.songs.update_one({"id": id}, {"$set": song_ext })
            song = db.songs.find_one({"id": id})
            song = json_util.dumps(song)          
            return song,200