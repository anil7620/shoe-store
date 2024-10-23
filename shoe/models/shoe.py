from shoe import mongo
from bson import ObjectId
from datetime import datetime
from shoe.models.ShoeVariant import ShoeVariant

class Shoe:
    collection = mongo.db.shoes

    @classmethod
    def get_all(cls):
        return list(cls.collection.find({}))

    @classmethod
    def create(cls, data):
        variants = data.pop('variants', [])
        result = cls.collection.insert_one(data)
        shoe_id = str(result.inserted_id)
        for variant in variants:
            variant['shoe_id'] = shoe_id
            ShoeVariant.create(variant)
        return shoe_id

    @classmethod
    def get_by_id(cls, id):
        shoe_id = ObjectId(id)
        shoe = cls.collection.find_one({"_id": shoe_id})
        
        if shoe: 
            shoe['variants'] = ShoeVariant.get_by_shoe_id(id)
        return shoe

    @classmethod
    def update(cls, id, data):
        id = ObjectId(id)
        variants = data.pop('variants', [])
        result = cls.collection.update_one({"_id": id}, {"$set": data})
        ShoeVariant.update_by_shoe_id(id, [{"shoe_id": str(id), **variant} for variant in variants])
        return result

    @classmethod
    def delete(cls, id):
        shoe_id = ObjectId(id)
        ShoeVariant.delete_by_shoe_id(id)
        return cls.collection.delete_one({"_id": shoe_id})
