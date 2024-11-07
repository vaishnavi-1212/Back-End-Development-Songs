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
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"})

@app.route('/count', methods=['GET'])
def get_count():
    # The count value (you can modify this as needed)
    count_value = 20
    return jsonify({'count': count_value}), 200

@app.route('/song', methods=['GET'])
def songs():
    try:
        # Fetch all documents from the 'songs' collection
        songs = db.songs.find({})

        # Convert the result to a list of songs
        song_list = []
        for song in songs:
            song['_id'] = str(song['_id'])  # Convert ObjectId to string
            song_list.append(song)

        return jsonify({'songs': song_list}), 200  # Return the songs as JSON

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/song/<int:id>', methods=['GET'])
def get_song_by_id(id):
    try:
        # Fetch the song from the database by its id
        song = db.songs.find_one({"id": id})

        # If the song is not found, return an error message
        if song is None:
            return jsonify({"message": "song with id not found"}), 404

        # Convert the MongoDB _id to string for JSON compatibility
        song['_id'] = str(song['_id'])

        # Return the song as a JSON response
        return jsonify(song), 200

    except Exception as e:
        # Return an error message in case of failure
        return jsonify({"error": str(e)}), 500

@app.route('/song', methods=['POST'])
def create_song():
    try:
        # Extract the song data from the request body (JSON format)
        song_data = request.get_json()

        # Check if the song with the same id already exists
        existing_song = db.songs.find_one({"id": song_data['id']})

        if existing_song:
            # If the song already exists, return a 302 Found with a message
            return jsonify({"Message": f"song with id {song_data['id']} already present"}), 302

        # Insert the new song into the database
        result = db.songs.insert_one(song_data)

        # Return the inserted song's ID as a response
        return jsonify({"inserted id": str(result.inserted_id)}), 201

    except Exception as e:
        # Handle any exceptions and return an error response
        return jsonify({"error": str(e)}), 500

@app.route('/song/<int:id>', methods=['PUT'])
def update_song(id):
    try:
        # Extract the updated song data from the request body (JSON format)
        updated_song_data = request.get_json()

        # Find the song by id in the database
        song = db.songs.find_one({"id": id})

        if not song:
            # If the song does not exist, return a 404 error with a message
            return jsonify({"message": "song not found"}), 404

        # Update the song with the provided data using $set to only update fields
        update_result = db.songs.update_one(
            {"id": id},  # Find the song by id
            {"$set": updated_song_data}  # Set the new song data
        )

        # Check if any updates were made
        if update_result.matched_count > 0 and update_result.modified_count > 0:
            return jsonify(updated_song_data), 200  # Return updated song data with HTTP 200 OK
        else:
            return jsonify({"message": "song found, but nothing updated"}), 200  # No changes were made

    except Exception as e:
        # Handle any exceptions and return an error response
        return jsonify({"error": str(e)}), 500

@app.route('/song/<int:id>', methods=['DELETE'])
def delete_song(id):
    try:
        # Delete the song by id
        delete_result = db.songs.delete_one({"id": id})

        if delete_result.deleted_count == 0:
            # If no song was deleted, return a 404 error with a message
            return jsonify({"message": "song not found"}), 404

        # If the song is successfully deleted, return an empty response with HTTP 204 No Content
        return '', 204

    except Exception as e:
        # Handle any exceptions and return an error response
        return jsonify({"error": str(e)}), 500
