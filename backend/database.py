from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        # Extract DB name from URI or default
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        # Standard uri: mongodb://host:port/dbname. If dbname is not in URI, default to education_platform
        db_name = settings.MONGO_URI.split("/")[-1].split("?")[0]
        if not db_name:
            db_name = "education_platform"
        self.db = self.client[db_name]
        print(f"Connected to MongoDB database: {db_name}")

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

db_client = Database()

def get_db():
    return db_client.db

def get_collection(name: str):
    return db_client.db[name]
