from shoe import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from bson import ObjectId

class Order:
    collection = mongo.db.orders

    @classmethod
    def get_by_buyer_id(cls, buyer_id):
        return list(cls.collection.find({"buyer_id": buyer_id}))


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
    def get_all_pending_by_buyer(cls, buyer_id):
        return list(cls.collection.find({"buyer_id": buyer_id, "status": "pending"}))
    
    @classmethod
    def get_pending_shoes_count_for_buyer(cls, buyer_id):
        return cls.collection.count_documents({"buyer_id": buyer_id, "status": "pending"})
    

    @classmethod
    def update_status(cls, buyer_id, order_id, status):
        return cls.collection.update_one({"_id": ObjectId(order_id), "buyer_id": buyer_id}, {"$set": {"status": status}})
    

    @classmethod
    def get_orders_for_buyer(cls, buyer_id):
        return list(cls.collection.find({"buyer_id": buyer_id}))
    

    @classmethod
    def update_status_emp(cls, order_id, status):
        return cls.collection.update_one({"order_id": order_id}, {"$set": {"status": status}})
    

    @classmethod
    def get_order_by_id(cls, order_id):
        return cls.collection.find_one({"order_id": order_id})