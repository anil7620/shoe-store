from flask import render_template, request, redirect, url_for, session, flash
from shoe import shoe
from .decorators import login_required
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId 
from flask import jsonify 
from shoe.models.user import User 
from shoe.models.payment import Payment 
from shoe.models.order import Order
from shoe.models.product import Shoe
from shoe.models.admin import Admin
from werkzeug.security import generate_password_hash, check_password_hash



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shoe.route('/admin_reg', methods=['GET'])
def admin_reg():
    try:
        # Hard-coded admin data
        email = "admin@admin.com"
        user_name = "Admin User"
        phone = "123-456-7890"
        password = "123"

        # Check if the admin email is already registered
        if Admin.exists_by_email(email):
            return jsonify({"message": "Admin already registered. Check DB for details."}), 200

        # Data preparation
        data = {
            "user_name": user_name,
            "email": email,
            "phone": phone,
            "password": generate_password_hash(password)
        }

        # Create admin record
        Admin.create(data)
        return jsonify({"message": "Admin registered successfully!"}), 201

    except Exception as e:
        logger.error(f"Error during admin registration: {str(e)}")
        return "Internal Server Error", 500



@shoe.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        
        # Check if user exists in the admin database
        if Admin.exists_by_email(email):
            admin = Admin.get_by_email(email)
            if check_password_hash(admin['password'], password):
                session["user_id"] = str(admin['_id'])
                session["user_type"] = "admin"
                return redirect(url_for('admin_dashboard'))
            else:
                return "Invalid credentials", 400
        else:
            return "No such admin", 404

    return render_template('admin/login.html')


@shoe.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_login'))
    products = Shoe.get_all()
    return render_template('admin/admin_dashboard.html', products=products)
 



# view all users

@shoe.route('/admin_view_users', methods=['GET'])
@login_required
def admin_view_users():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_dashboard'))

    users = User.get_all()  # Replace with the actual method call to get all users
    users = list(users)
    return render_template('admin/view_users.html', users=users)



@shoe.route('/admin_view_payments', methods=['GET'])
@login_required
def admin_view_payments():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_dashboard'))

    payments = Payment.find_all()  # Replace with the actual method call to get all payment records
    payments = list(payments)
    return render_template('admin/view_payments.html', payments=payments)




@shoe.route('/view_orders')
@login_required
def view_orders():
    orders = Order.get_all()  # Assuming this method fetches all orders
    cart = session.get('cart', [])
    cart_count = len(cart)

    # Get product names and user names for each order
    for order in orders:
        cart_items = order['cart']
        product_details = []
        for item in cart_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            product = Shoe.get_by_id(product_id)
            if product:
                product_details.append({
                    "shoe_name": product['shoe_name'],
                    "quantity": quantity
                })
        order['product_details'] = product_details

        user = User.get_by_id(order['user_id'])
        order['user_name'] = f"{user['first_name']}" if user else "Unknown User"

    return render_template('orders/view_orders.html', orders=orders, cart_count=cart_count)


@shoe.route('/admin_view_orders', methods=['GET', 'POST'])
@login_required
def admin_view_orders():
    if session["user_type"] != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        new_status = request.form.get('status')
        Order.update(order_id, {"status": new_status})
        flash("Order status updated successfully.", "success")
        return redirect(url_for('admin_view_orders'))
    
    orders = Order.get_all()  # Assuming this method fetches all orders
    cart = session.get('cart', [])
    cart_count = len(cart)

    # Get product names and user names for each order
    for order in orders:
        cart_items = order['products']
        product_details = []
        for item in cart_items:
            product = item.get('product')
            quantity = item.get('quantity')
            if product:
                product_details.append({
                    "shoe_name": product['shoe_name'],
                    "quantity": quantity
                })
        order['product_details'] = product_details
        user = User.get_by_id(order['user_id'])
        order['user_name'] = f"{user['first_name']}" if user else "Unknown User"
    return render_template('admin/view_orders.html', orders=orders, cart_count=cart_count)
