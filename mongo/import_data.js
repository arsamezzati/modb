const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/docker-entrypoint-initdb.d/it.json', 'utf8'));

db = db.getSiblingDB('cities');

db.cities.drop();
db.cities.insertMany(data);

print("Data import completed.");
