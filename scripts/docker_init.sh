#!/bin/bash

# Wait for MySQL to be ready
echo "Waiting for MySQL..."
until mysqladmin ping -h mysql_container --silent; do
    sleep 1
done
echo "MySQL is ready!"

# Execute SQL scripts
mysql -h mysql_container -u root -proot_password < /docker-entrypoint-initdb.d/sql/01_create_database.sql
mysql -h mysql_container -u root -proot_password < /docker-entrypoint-initdb.d/sql/02_create_tables.sql
mysql -h mysql_container -u root -proot_password < /docker-entrypoint-initdb.d/sql/03_insert_data.sql
echo "MySQL initialization scripts executed."

# Wait for Neo4j to be ready
echo "Waiting for Neo4j..."
until curl -s http://neo4j_container:7474; do
    sleep 1
done
echo "Neo4j is ready!"

# Run the data transfer script
python /scripts/data_transfer.py
echo "Data transfer script executed."
