import os
import ssl
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsAllowInvalidHostnames=True,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000
)

db = client["stock_advisor_ai"]

users_collection     = db["users"]
portfolio_collection = db["portfolios"]
chat_collection      = db["ai_chats"]
news_cache_collection = db["news_cache"]