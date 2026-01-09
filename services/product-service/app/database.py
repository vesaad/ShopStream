from pymongo import MongoClient
import os

# Merr URI nga environment
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:admin123@mongodb:27017/"
)

# Krijo client dhe database
client = MongoClient(MONGO_URI)
db = client.shopstream

# Krijo objekt mongodb që përdoret në main.py
class MongoDB:
    def __init__(self):
        self.products = db.products
        self.shopping_carts = db.shopping_carts
        self.inventory = db.inventory

# Ky është ai që importohet në main.py
mongodb = MongoDB()

print("✅ MongoDB client initialized")
