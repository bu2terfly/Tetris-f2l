import motor.motor_asyncio
from config import DB_NAME, DB_URI

# Configuration
DATABASE_NAME = DB_NAME
DATABASE_URI = DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        # Initialize MongoDB client and collections for users and groups
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users  # User collection
        self.grp = self.db.groups  # Group collection

    # Template for new user entry
    def new_user(self, id, name):
        return dict(
            id=id,
            name=name,
            is_subscribed=False,  # Track whether the user is subscribed to the channel
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
            approved=False  # Add approval status to the user entry
        )

    # Template for new group entry
    def new_group(self, id, title):
        return dict(
            id=id,
            title=title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
        )

    # Add a new user to the database
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    # Check if a user exists in the database
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    # Count the total number of users in the database
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    # Fetch all users in the database
    async def get_all_users(self):
        return self.col.find({})

    # Delete a user from the database
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    # Check if a user is subscribed to the update channel
    async def is_user_subscribed(self, user_id):
        """Check if the user is subscribed to the update channel"""
        user = await self.col.find_one({'id': int(user_id)})
        if user:
            return user.get('is_subscribed', False)
        return False

    # Update the user's subscription status
    async def update_subscription_status(self, user_id, status=True):
        """Update the subscription status of the user"""
        await self.col.update_one({'id': int(user_id)}, {'$set': {'is_subscribed': status}})

    # Group operations: add, check existence, etc.
    async def add_group(self, id, title):
        group = self.new_group(id, title)
        await self.grp.insert_one(group)

    async def is_group_exist(self, id):
        group = await self.grp.find_one({'id': int(id)})
        return bool(group)

    async def total_groups_count(self):
        count = await self.grp.count_documents({})
        return count

    async def get_all_groups(self):
        return self.grp.find({})

    async def delete_group(self, group_id):
        await self.grp.delete_many({'id': int(group_id)})

# Instantiate the database object
db = Database(DATABASE_URI, DATABASE_NAME)
