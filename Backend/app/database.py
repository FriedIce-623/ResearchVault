from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME") or "researchvault"

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]

papers = db["papers"]
datasets = db["datasets"]