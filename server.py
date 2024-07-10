from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import requests

app = Flask(__name__)

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = None

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_regions(self):
        with self.driver.session() as session:
            result = session.read_transaction(self._get_regions)
            return [record["name"] for record in result]

    def get_cities_in_region(self, region):
        with self.driver.session() as session:
            result = session.read_transaction(self._get_cities_in_region, region)
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
    print(cities)
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
    city = request.args.get('city')
    response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=your_openweathermap_api_key")
    if response.status_code == 200:
        weather_data = response.json()
        temperature = weather_data["main"]["temp"] - 273.15  # Convert from Kelvin to Celsius
        return jsonify({"city": city, "temperature": temperature})
    else:
        return jsonify({"error": "City not found or error fetching data"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
