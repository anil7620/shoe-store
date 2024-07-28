from flask import render_template, request, redirect, url_for, session
from shoe import shoe
from shoe.models.user import User
from shoe.models.product import Shoe
from shoe.models.category import Category
from shoe.models.ShoeVariant import ShoeVariant

from shoe.models.admin import Admin
from werkzeug.security import generate_password_hash, check_password_hash 
import logging
from bson import ObjectId
from .decorators import login_required
from flask import send_from_directory

from flask import flash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shoe.route('/')
def index():
    products = Shoe.get_all()
    cart = session.get('cart', [])
    cart_count = len(cart)
    product_ids = [str(product['_id']) for product in products]
    product_variants = ShoeVariant.get_by_shoe_ids(product_ids)

    # Organize variants by shoe_id
    variants_by_shoe_id = {}
    for variant in product_variants:
        shoe_id = variant['shoe_id']
        if shoe_id not in variants_by_shoe_id:
            variants_by_shoe_id[shoe_id] = []
        variants_by_shoe_id[shoe_id].append(variant)

    # Add variants to products
    for product in products:
        product_id = str(product['_id'])
        product['variants'] = variants_by_shoe_id.get(product_id, [])
        product['in_stock'] = any(variant['stock'] > 0 for variant in product['variants'])

    return render_template('index.html', products=products, cart_count=cart_count)


@shoe.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(shoe.config['UPLOAD_FOLDER'], filename)

import random
@shoe.route('/user_dashboard')
@login_required
def user_dashboard():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for('user_login'))
    
    products = Shoe.get_all()  # Fetch all products
    cart = session.get('cart', [])
    cart_count = len(cart)

    # Fetch variants for all shoes and map them by shoe_id
    shoe_ids = [str(product['_id']) for product in products]
    variants = ShoeVariant.get_by_shoe_ids(shoe_ids)
    variants_by_shoe_id = {}
    for variant in variants:
        shoe_id = variant['shoe_id']
        if shoe_id not in variants_by_shoe_id:
            variants_by_shoe_id[shoe_id] = []
        variants_by_shoe_id[shoe_id].append(variant)

    # Process products to include the stock information from variants
    for product in products:
        shoe_id = str(product['_id'])
        product_variants = variants_by_shoe_id.get(shoe_id, [])
        in_stock = any(variant.get('stock', 0) > 0 for variant in product_variants)
        product['in_stock'] = in_stock
        product['variants'] = product_variants  # Add variants to the product data

    return render_template('index.html', session=session, products=products, cart_count=cart_count)


#     return render_template('users/login.html')
@shoe.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        
        # Check if user exists in the user database
        if User.exists_by_email(email):
            user = User.get_by_email(email)
            if check_password_hash(user['password'], password):
                session["user_id"] = str(user['_id'])
                session["user_type"] = "user"
                next_page = session.get('next', url_for('user_dashboard'))
                session.pop('next', None)  # Remove 'next' from session after using it
                return redirect(next_page)
            else:
                flash('Invalid credentials', 'error')
        else:
            flash('No such user', 'error')

    next_page = request.args.get('next')
    if next_page:
        session['next'] = next_page  # Store the next page URL in the session

    return render_template('user/login.html')





@shoe.route('/register_user', methods=['GET', 'POST'])
def register_user(): 
    try:
        if request.method == 'POST':
            email = request.form.get("email").strip()
            if User.exists_by_email(email):
                return "Email already registered", 400

            password = request.form.get("password").strip()
            confirm_password = request.form.get("confirm_password").strip()

            if password != confirm_password:
                return "Passwords do not match", 400

            data = {
                "first_name": request.form.get("first_name").strip(),
                "date_of_birth": request.form.get("date_of_birth").strip(),
                "city": request.form.get("city").strip(),
                "zip_code": request.form.get("zip_code").strip(),
                "email": email,
                "phone_number": request.form.get("phone_number").strip(),
                "address": request.form.get("address").strip(),
                "password": generate_password_hash(password)
            } 
            User.create(data)
            return redirect(url_for('user_login'))

        return render_template('user/register_user.html')
    except Exception as e:
        logger.error(f"Error during user registration: {str(e)}")
        return "Internal Server Error", 500
 
@shoe.route('/logout')
def logout():
    try:
        session.clear()  
        session.pop('user_id', None)
        session.pop('user_type', None)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return "Internal Server Error", 500



 