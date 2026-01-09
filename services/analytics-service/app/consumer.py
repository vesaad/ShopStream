from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import os
from datetime import datetime
import time

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@mongodb:27017/")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")

print("Starting Analytics Consumer...")
print(f"Connecting to Kafka: {KAFKA_BROKER}")
print(f"Connecting to MongoDB: {MONGO_URI[:30]}...")

# Wait for Kafka to be ready
time.sleep(10)

# MongoDB connection
try:
    client = MongoClient(MONGO_URI)
    db = client.shopstream
    analytics_collection = db.analytics_data
    print("MongoDB connected")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    exit(1)

# Kafka consumer for all topics
try:
    consumer = KafkaConsumer(
        'user-events',
        'product-events',
        'order-events',
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='analytics-group',
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    print("Kafka consumer connected")
    print("Listening for events on: user-events, product-events, order-events")
except Exception as e:
    print(f"Kafka connection failed: {e}")
    print("Analytics will continue but won't receive events")
    # Don't exit, let API run
    while True:
        time.sleep(60)

# Consume messages
for message in consumer:
    try:
        event = message.value
        topic = message.topic
        
        # Create analytics document
        analytics_doc = {
            "topic": topic,
            "event_type": event.get("event_type"),
            "data": event.get("data"),
            "timestamp": datetime.fromisoformat(event.get("timestamp")) if event.get("timestamp") else datetime.utcnow(),
            "processed_at": datetime.utcnow(),
            "partition": message.partition,
            "offset": message.offset
        }
        
        # Insert into MongoDB
        analytics_collection.insert_one(analytics_doc)
        
        print(f"Processed: {topic} -> {event.get('event_type')}")
        
    except Exception as e:
        print(f"Error processing message: {e}")
