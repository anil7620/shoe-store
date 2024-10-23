from shoe import mongo
from werkzeug.security import generate_password_hash, check_password_hash

class Payment:
    collection = mongo.db.payments



    @classmethod
    def find_all(cls):
        return list(cls.collection.find({}))


    @classmethod
    def save(cls, data):
        try:
            cls.collection.insert_one(data)
            return True
        except Exception as e:
            raise e