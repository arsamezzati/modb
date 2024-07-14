from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import requests
import mysql.connector
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

weatherurl = "https://api.tomorrow.io/v4/weather/realtime?location="
weatherapikey = "KRJlkz6Y1kCkKtx8TguBn32L0Ul02gHM"
headers = {"accept": "application/json"}

app = Flask(__name__)

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = None

# MySQL connection details
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3307  # Updated port
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root_password'
MYSQL_DB = 'modb'

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27018/"
MONGO_DB = "cities"
MONGO_COLLECTION = "historical"

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
mongo_collection = mongo_db[MONGO_COLLECTION]


class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_regions(self):
        with self.driver.session() as session:
            result = session.execute_read(self._get_regions)
            return [record["name"] for record in result]

    def get_cities_in_region(self, region):
        with self.driver.session() as session:
            result = session.execute_read(self._get_cities_in_region, region)
            return [record["name"] for record in result]

    def add_place(self, region, city):
        with self.driver.session() as session:
            session.write_transaction(self._create_city_and_region, region, city)

    @staticmethod
    def _get_regions(tx):
        query = "MATCH (r:Region) RETURN r.name AS name"
        return tx.run(query).data()

    @staticmethod
    def _get_cities_in_region(tx, region):
        query = """
            MATCH (r:Region)<-[:LOCATED_IN]-(c:City)
            WHERE r.name = $region
            RETURN c.name AS name
        """
        return tx.run(query, region=region).data()

    @staticmethod
    def _create_city_and_region(tx, region, city):
        tx.run("""
            MERGE (r:Region {name: $region})
            MERGE (c:City {name: $city})
            MERGE (c)-[:LOCATED_IN]->(r)
        """, region=region, city=city)


db = Neo4jDatabase(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


@app.route('/regions', methods=['GET'])
def get_regions():
    regions = db.get_regions()
    return jsonify(regions)


@app.route('/cities', methods=['GET'])
def get_cities():
    region = request.args.get('region')
    cities = db.get_cities_in_region(region)
    return jsonify(cities)


@app.route('/add_place', methods=['POST'])
def add_place():
    data = request.json
    region = data.get('region')
    city = data.get('city')
    db.add_place(region, city)
    return jsonify({"message": "Place added successfully"}), 201


@app.route('/temperature', methods=['GET'])
def get_temperature():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "User not provided"}), 401

    city = request.args.get('city')
    response = requests.get(f"{weatherurl}{city}&apikey={weatherapikey}", headers=headers)
    if response.status_code == 200:
        weather_data = response.json()
        weather_data["date"] = datetime.utcnow()
        weather_data["username"] = username
        result = mongo_collection.insert_one(weather_data)
        print(result)
        print(weather_data)
        temperature_data = {
            "city": city,
            "temperature": weather_data["data"]["values"]["temperature"],
            "humidity": weather_data["data"]["values"]["humidity"],
            "pressure": weather_data["data"]["values"]["pressureSurfaceLevel"],
            "wind_speed": weather_data["data"]["values"]["windSpeed"],
            "visibility": weather_data["data"]["values"]["visibility"],
            "id": str(result.inserted_id)
        }
        return jsonify(temperature_data)
    else:
        return jsonify({"error": "City not found or error fetching data"}), 404


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    username = data.get('username')
    password = data.get('password')
    user_type = data.get('type', 1)  # Default to type 1 if not provided

    if not username or not password:
        return jsonify({"error": "Username or password not provided"}), 400

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, password, type) VALUES (%s, %s, %s)",
                       (username, password, user_type))
        conn.commit()
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 400
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "User created successfully"}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username or password not provided"}), 400

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and user[0] == password:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/history', methods=['GET'])
def history():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "User not provided"}), 401

    history_data = list(mongo_collection.find({"username": username}, {"_id": 0}))
    return jsonify(history_data), 200


@app.route('/favorites', methods=['GET'])
def get_favorites():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "User not provided"}), 401

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    cursor.execute("SELECT item FROM favorites WHERE user_id = (SELECT id FROM users WHERE username = %s)", (username,))
    favorites = cursor.fetchall()
    cursor.close()
    conn.close()

    # Fetch details from MongoDB
    favorite_details = []
    for favorite in favorites:
        mongo_id = favorite[0]
        mongo_data = mongo_collection.find_one({"_id": ObjectId(mongo_id)})
        if mongo_data:
            mongo_data["_id"] = str(mongo_data["_id"])  # Convert ObjectId to string for JSON serialization
            favorite_details.append(mongo_data)

    return jsonify(favorite_details), 200


@app.route('/favorites/add', methods=['POST'])
def add_favorite():
    data = request.json
    username = data.get('username')
    item = data.get('item')

    if not username or not item:
        return jsonify({"error": "User or item not provided"}), 400

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    cursor.execute("INSERT INTO favorites (user_id, item) VALUES ((SELECT id FROM users WHERE username = %s), %s)",
                   (username, item))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Favorite added successfully"}), 201


@app.route('/favorites/remove', methods=['POST'])
def remove_favorite():
    data = request.json
    username = data.get('username')
    item = data.get('item')

    if not username or not item:
        return jsonify({"error": "User or item not provided"}), 400

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()

    cursor.execute("DELETE FROM favorites WHERE user_id = (SELECT id FROM users WHERE username = %s) AND item = %s",
                   (username, item))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Favorite removed successfully"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
