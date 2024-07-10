from pymongo import MongoClient

# Replace the following with your MongoDB connection string
client = MongoClient("mongodb://root:1234@localhost:27017/")

# Create a database
db = client['mydatabase']

# Create a collection
collection = db['mycollection']

document = {"name": "John", "age": 30, "city": "New York"}
collection.insert_one(document)

# Insert multiple documents
documents = [
    {"name": "Anna", "age": 25, "city": "London"},
    {"name": "Mike", "age": 32, "city": "Chicago"}
]
collection.insert_many(documents)

print("Database, collection, and documents created successfully")
