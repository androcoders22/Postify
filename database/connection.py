"""
MongoDB connection and utilities.
"""
import base64
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

# MongoDB Connection
_client = None
_db = None
_collection = None


def get_client():
    """Get or create MongoDB client."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


def get_database():
    """Get the postify database."""
    global _db
    if _db is None:
        _db = get_client().get_database("postify")
    return _db


def get_collection():
    """Get the users collection."""
    global _collection
    if _collection is None:
        _collection = get_database().get_collection("users")
    return _collection


def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict."""
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    if "logo" in doc and isinstance(doc["logo"], bytes):
        doc["logo"] = base64.b64encode(doc["logo"]).decode("utf-8")
    return doc


_subscribers_collection = None


def get_subscribers_collection():
    """Get the subscribers collection."""
    global _subscribers_collection
    if _subscribers_collection is None:
        _subscribers_collection = get_database().get_collection("subscribers")
    return _subscribers_collection


def serialize_subscriber_doc(doc):
    """Convert MongoDB subscriber document to JSON-serializable dict."""
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc
