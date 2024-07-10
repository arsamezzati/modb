from pymongo import MongoClient
from neo4j import GraphDatabase

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27018/"
MONGO_DB = "cities"
MONGO_COLLECTION = "cities"

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = None


def extract_data_from_mongo(mongo_uri, mongo_db, mongo_collection):
    print("Connecting to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    collection = db[mongo_collection]

    # Extract city, admin_name, and capital
    print("Extracting data from MongoDB...")
    cities_data = collection.find({}, {"city": 1, "admin_name": 1, "capital": 1, "_id": 0})
    transformed_data = [(city_data.get("city"), city_data.get("admin_name"), city_data.get("capital")) for city_data in
                        cities_data]

    client.close()
    print(f"Extracted {len(transformed_data)} records from MongoDB")
    return transformed_data


def clear_neo4j(neo4j_uri, neo4j_user, neo4j_password):
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def delete_all(tx):
        print("Deleting all nodes and relationships in Neo4j...")
        tx.run("MATCH (n) DETACH DELETE n")

    with driver.session() as session:
        session.execute_write(delete_all)

    driver.close()


def load_data_to_neo4j(neo4j_uri, neo4j_user, neo4j_password, data):
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    def create_city_and_region(tx, city, admin_name, capital):
        print(f"Inserting {city}, {admin_name}, {capital} into Neo4j")
        city_type = "minor"
        if capital == "admin":
            city_type = "region capital"
        elif capital == "primary":
            city_type = "country capital"

        tx.run("""
            MERGE (r:Region {name: $admin_name})
            MERGE (c:City {name: $city, type: $city_type})
            MERGE (c)-[:LOCATED_IN]->(r)
        """, admin_name=admin_name, city=city, city_type=city_type)

    with driver.session() as session:
        for city, admin_name, capital in data:
            session.execute_write(create_city_and_region, city, admin_name, capital)

    driver.close()


# Main execution
print("Starting data extraction and loading process...")
mongo_data = extract_data_from_mongo(MONGO_URI, MONGO_DB, MONGO_COLLECTION)
print("Extracted data:", mongo_data)
clear_neo4j(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
load_data_to_neo4j(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, mongo_data)
print("Data loading to Neo4j completed.")
