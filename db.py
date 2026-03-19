import motor.motor_asyncio
import os

# Default to localhost if not specified
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    db = client.linux_lifesaver
    print(f"✅ Connected to MongoDB at {MONGO_URI}")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    db = None