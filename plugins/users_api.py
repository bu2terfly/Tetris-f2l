import requests
import json
from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

client = AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
col = db["users"]

# Function to get the shortened link using the user's shortener API and base site
async def get_short_link(user, link):
    api_key = user["shortener_api"]
    base_site = user["base_site"]
    
    # If base_site is None, return None or handle appropriately
    if not base_site:
        return None
    
    response = requests.get(f"https://{base_site}/api?api={api_key}&url={link}")
    data = response.json()

    if data["status"] == "success" or response.status_code == 200:
        return data["shortenedUrl"]

# Function to retrieve the user from the database or create a new one if not found
async def get_user(user_id):

    user_id = int(user_id)

    user = await col.find_one({"user_id": user_id})

    if not user:
        res = {
            "user_id": user_id,
            "shortener_api": None,
            "base_site": None,
        }

        await col.insert_one(res)
        user = await col.find_one({"user_id": user_id})

    return user

# Function to update user information, including base_site
async def update_user_info(user_id, value: dict):
    user_id = int(user_id)
    myquery = {"user_id": user_id}
    
    # If the user wants to remove base_site, set it to None in the database
    if "base_site" in value and value["base_site"] == "None":
        value["base_site"] = None  # Remove the base_site by setting it to None
    
    newvalues = { "$set": value }
    await col.update_one(myquery, newvalues)

# Function to get the total number of users
async def total_users_count():
    count = await col.count_documents({})
    return count

# Function to retrieve all users
async def get_all_users():
    all_users = col.find({})
    return all_users

# Function to delete a user from the database
async def delete_user(user_id):
    await col.delete_one({'user_id': int(user_id)})
    
