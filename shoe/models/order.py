from shoe import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId

class Order:
    collection = mongo.db.orders

    @classmethod
    def get_by_user_id(cls, user_id):
        return list(cls.collection.find({"user_id": user_id}))


    @classmethod
    def get_all(cls):
        return list(cls.collection.find({}))
    

    @classmethod
    def update(cls, order_id, data):
        return cls.collection.update_one({"_id": ObjectId(order_id)}, {"$set": data})
    
    @classmethod
    def save(cls, data):
        return cls.collection.insert_one(data)
    
    # get all pending stockout out for delivery orders
    @classmethod
    def get_all_pending_orders(cls):
        return list(cls.collection.find({"status": {"$in": ["pending", "stockout", "out_for_delivery"]}}))
    

    @classmethod
    def get_all_pending_by_user(cls, user_id):
        return list(cls.collection.find({"user_id": user_id, "status": "pending"}))
    
    @classmethod
    def get_pending_products_count_for_user(cls, user_id):
        return cls.collection.count_documents({"user_id": user_id, "status": "pending"})
    

    @classmethod
    def update_status(cls, user_id, order_id, status):
        return cls.collection.update_one({"_id": ObjectId(order_id), "user_id": user_id}, {"$set": {"status": status}})
    

    @classmethod
    def get_orders_for_user(cls, user_id):
        return list(cls.collection.find({"user_id": user_id}))
    

    @classmethod
    def update_status_emp(cls, order_id, status):
        return cls.collection.update_one({"order_id": order_id}, {"$set": {"status": status}})
    

    @classmethod
    def get_order_by_id(cls, order_id):
        return cls.collection.find_one({"order_id": order_id})