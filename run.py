from shoe import shoe
from shoe.routes import  admin_routes, auth, category_routes, order_routes, product_routes
from shoe.routes import payment_routes
if __name__ == "__main__":
     shoe.run(host='0.0.0.0', port=5000, debug=True)

