

from shoe import mongo
from bson import ObjectId

class Cart:
    collection = mongo.db.cart

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.collection.find_one({"user_id": ObjectId(user_id)})

    @classmethod
    def save_cart(cls, user_id, items):
        cls.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": {"items": items}},
            upsert=True
        )


    @classmethod
    def clear_cart(cls, user_id):
        cls.collection.delete_one({"user_id": ObjectId(user_id)})