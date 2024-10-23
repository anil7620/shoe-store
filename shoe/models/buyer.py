from shoe import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId, errors

class Buyer:
    collection = mongo.db.buyers

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)


    @classmethod
    def get_by_id(cls, buyer_id):
        return cls.collection.find_one({"_id": ObjectId(buyer_id)})

    @classmethod
    def get_by_email(cls, email):
        return cls.collection.find_one({"email": email})

    @classmethod
    def check_password(cls, buyer, password):
        return check_password_hash(buyer["password"], password)

    @classmethod
    def exists_by_email(cls, email):
        return cls.collection.find_one({"email": email}) is not None

    @classmethod
    def get_buyer_name_by_id(cls, buyer_id):
        try:
            buyer = cls.collection.find_one({"_id": ObjectId(buyer_id)})  
            return buyer['name'] if buyer else None
        except errors.PyMongoError as e: 
            return None

    @classmethod
    def get_buyer_by_id(cls, buyer_id):
        try:
            buyer = cls.collection.find_one({"_id": ObjectId(buyer_id)})  
            return buyer
        except errors.PyMongoError as e: 
            return None
    @classmethod
    def get_all(cls):
        return cls.collection.find({})
    
    @classmethod
    def find_all(cls):
        return cls.collection.find({})
    
    

    