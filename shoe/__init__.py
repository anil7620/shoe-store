from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
import os
import certifi

ca = certifi.where()

shoe = Flask(__name__, template_folder='templates', static_folder='static')
UPLOAD_FOLDER = os.path.join(shoe.root_path, 'static', 'uploads')  # Use os.path.join to get the absolute path
shoe.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure MongoDB URI and JWT
shoe.config["MONGO_URI"] = "mongodb+srv://axk68420:JGWE4RdbICzCBjNV@cluster0.x6ffwl7.mongodb.net/shoe_store?retryWrites=true&w=majority"
shoe.config['JWT_SECRET_KEY'] = "adb"
shoe.secret_key = 'shoe'

# Initialize PyMongo with tlsCAFile
shoe.config["MONGO_OPTIONS"] = {
    "tlsCAFile": ca
}
mongo = PyMongo(shoe, tlsCAFile=ca)

# Initialize JWT Manager
jwt = JWTManager(shoe)

# Your routes and other configurations...

if __name__ == "__main__":
    shoe.run(host='0.0.0.0', port=5000, debug=True)
