from pymongo import MongoClient
from app.config import settings

class MongoDB:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client.shopstream
        
        # Collections
        self.analytics_data = self.db.analytics_data

mongodb = MongoDB()
