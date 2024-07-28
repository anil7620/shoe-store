from shoe import mongo
from bson import ObjectId

class ShoeVariant:
    collection = mongo.db.shoe_variants

    @classmethod
    def create(cls, data):
        result = cls.collection.insert_one(data)
        return str(result.inserted_id)  # Convert ObjectId to string if necessary
    

    @classmethod
    def update(cls, id, data):
        variant_id = ObjectId(id)
        return cls.collection.update_one({"_id": variant_id}, {"$set": data})
    
    @classmethod
    def get_by_id(cls, id):
        variant_id = ObjectId(id)
        return cls.collection.find_one({"_id": variant_id})

    @classmethod
    def find_one(cls, query):
        return cls.collection.find_one(query)

    @classmethod
    def get_by_shoe_id(cls, shoe_id):
        shoe_id = str(shoe_id) 
        return list(cls.collection.find({"shoe_id": shoe_id}))

    @classmethod
    def get_by_shoe_ids(cls, shoe_ids):
        # Convert ObjectId to string if necessary
        shoe_ids = [str(shoe_id) for shoe_id in shoe_ids] 
        return list(cls.collection.find({"shoe_id": {"$in": shoe_ids}}))

    @classmethod
    def delete_by_shoe_id(cls, shoe_id):
        shoe_id = ObjectId(shoe_id)
        return cls.collection.delete_many({"shoe_id": shoe_id})
    

    @classmethod
    def update_by_shoe_id(cls, shoe_id, data):
        shoe_id = str(shoe_id)
        print('====',data)
        cls.collection.delete_many({"shoe_id": shoe_id})
        cls.collection.insert_many(data)


    @classmethod
    def count_by_shoe_id(cls, shoe_id):
        shoe_id = ObjectId(shoe_id)
        return cls.collection.count_documents({"shoe_id": shoe_id})
    
    @classmethod
    def sum_available_stock_by_shoe_id(cls, shoe_id):
        shoe_id = ObjectId(shoe_id)
        return sum([variant['stock'] for variant in cls.collection.find({"shoe_id": shoe_id})])
    


    

    @classmethod
    def get_variants_by_color_and_size(cls, shoe_id, color, size):
        shoe_id = str(shoe_id)
        return list(cls.collection.find({"shoe_id": shoe_id, "color": color, "size": size}))
    

    @classmethod
    def get_variants_by_color(cls, shoe_id, color):
        shoe_id = str(shoe_id)
        return list(cls.collection.find({"shoe_id": shoe_id, "color": color}))
    

    @classmethod
    def count_by_product_id(cls, product_id):
        return cls.collection.count_documents({"product_id": product_id})
    

    @classmethod
    def sum_available_stock_by_product_id(cls, product_id):
        return sum([variant['stock'] for variant in cls.collection.find({"product_id": product_id})])
    

    @classmethod
    def delete_many_by_product_id(cls, shoe_id):
        return cls.collection.delete_many({"shoe_id": shoe_id})
    
    @classmethod
    def delete_many(cls, query):
        return cls.collection.delete_many(query)