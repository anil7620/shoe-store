

from shoe import mongo
from bson import ObjectId

class Cart:
    collection = mongo.db.cart

    @classmethod
    def get_by_buyer_id(cls, buyer_id):
        return cls.collection.find_one({"buyer_id": ObjectId(buyer_id)})

    @classmethod
    def save_cart(cls, buyer_id, items):
        cls.collection.update_one(
            {"buyer_id": ObjectId(buyer_id)},
            {"$set": {"items": items}},
            upsert=True
        )


    @classmethod
    def clear_cart(cls, buyer_id):
        cls.collection.delete_one({"buyer_id": ObjectId(buyer_id)})