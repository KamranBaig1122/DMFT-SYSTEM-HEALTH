import os
from pymongo import MongoClient
from dotenv import load_dotenv
from bson.objectid import ObjectId
import logging

# Load environment variables
load_dotenv('config.env')

# MongoDB Configuration
class MongoDBConfig:
    def __init__(self):
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/dmft')
        self.database_name = os.getenv('DATABASE_NAME', 'dmft')
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            # Test connection
            self.client.admin.command('ping')
            print(f"Successfully connected to MongoDB: {self.database_name}")
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
    
    def get_database(self):
        """Get database instance"""
        if self.db is None:
            self.connect()
        return self.db
    
    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

# Global MongoDB instance
mongo_config = MongoDBConfig()

class MongoDBModels:
    def __init__(self):
        self.db = mongo_config.get_database()
        self.users_collection = self.db.users
        self.results_collection = self.db.results
        
        # Create indexes for better performance
        self.create_indexes()
    
    def create_indexes(self):
        """Create database indexes"""
        try:
            # Create unique index on email for users
            self.users_collection.create_index("email", unique=True)
            # Create index on doctor_id for results
            self.results_collection.create_index("doctor_id")
            print("Database indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {e}")
    
    # User operations
    def create_user(self, name, email, password, age, gender, profession):
        """Create a new user"""
        try:
            user_data = {
                "name": name,
                "email": email,
                "password": password,
                "age": age,
                "gender": gender,
                "profession": profession
            }
            result = self.users_collection.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def find_user_by_email(self, email):
        """Find user by email"""
        try:
            return self.users_collection.find_one({"email": email})
        except Exception as e:
            print(f"Error finding user by email: {e}")
            return None
    
    def find_user_by_id(self, user_id):
        """Find user by ID"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            return self.users_collection.find_one({"_id": user_id})
        except Exception as e:
            print(f"Error finding user by ID: {e}")
            return None
    
    def update_user(self, user_id, update_data):
        """Update user information"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id):
        """Delete user"""
        try:
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            result = self.users_collection.delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_users_by_profession(self, profession):
        """Get all users by profession"""
        try:
            return list(self.users_collection.find({"profession": profession}))
        except Exception as e:
            print(f"Error getting users by profession: {e}")
            return []
    
    # Results operations
    def create_result(self, doctor_id, patient_name, dmft_index, decayed_tooth, missing_tooth, filled_tooth):
        """Create a new result"""
        try:
            result_data = {
                "doctor_id": ObjectId(doctor_id) if isinstance(doctor_id, str) else doctor_id,
                "patient_name": patient_name,
                "dmft_index": dmft_index,
                "decayed_tooth": decayed_tooth,
                "missing_tooth": missing_tooth,
                "filled_tooth": filled_tooth
            }
            result = self.results_collection.insert_one(result_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating result: {e}")
            return None
    
    def get_results_by_doctor(self, doctor_id):
        """Get all results for a specific doctor"""
        try:
            if isinstance(doctor_id, str):
                doctor_id = ObjectId(doctor_id)
            return list(self.results_collection.find({"doctor_id": doctor_id}))
        except Exception as e:
            print(f"Error getting results by doctor: {e}")
            return []
    
    def get_all_results(self):
        """Get all results"""
        try:
            return list(self.results_collection.find())
        except Exception as e:
            print(f"Error getting all results: {e}")
            return []
    
    def delete_result(self, result_id, doctor_id=None):
        """Delete a result"""
        try:
            if isinstance(result_id, str):
                result_id = ObjectId(result_id)
            
            query = {"_id": result_id}
            if doctor_id:
                if isinstance(doctor_id, str):
                    doctor_id = ObjectId(doctor_id)
                query["doctor_id"] = doctor_id
            
            result = self.results_collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting result: {e}")
            return False
    
    def delete_results_by_doctor(self, doctor_id):
        """Delete all results for a specific doctor"""
        try:
            if isinstance(doctor_id, str):
                doctor_id = ObjectId(doctor_id)
            result = self.results_collection.delete_many({"doctor_id": doctor_id})
            return result.deleted_count
        except Exception as e:
            print(f"Error deleting results by doctor: {e}")
            return 0

# Global models instance
mongodb_models = MongoDBModels()
