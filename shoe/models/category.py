from shoe import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

class Category:
    collection = mongo.db.categories


    @classmethod
    def create(cls, data):
        cls.collection.insert_one(data)

    @classmethod
    def update(cls, category_id, data):
        category_id = ObjectId(category_id)
        cls.collection.update_one({"_id": category_id}, {"$set": data})

    @classmethod
    def delete(cls, category_id):
        category_id = ObjectId(category_id)
        cls.collection.delete_one({"_id": category_id})

    @classmethod
    def get_by_id(cls, category_id):
        category_id = ObjectId(category_id)
        return cls.collection.find_one({"_id": category_id})

    @classmethod
    def get_all(cls):
        return list(cls.collection.find({}))