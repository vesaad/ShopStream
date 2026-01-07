import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "shopstream")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

products = db["products"]
inventory = db["inventory"]
carts = db["shopping_carts"]
