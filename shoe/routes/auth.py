from flask import render_template, request, redirect, url_for, session
from shoe import shoe
from shoe.models.buyer import Buyer
from shoe.models.shoe import Shoe
from shoe.models.category import Category
from shoe.models.ShoeVariant import ShoeVariant
from shoe.models.admin import Admin
from werkzeug.security import generate_password_hash, check_password_hash 
import logging
from bson import ObjectId
from .decorators import login_required
from flask import send_from_directory
# import str

from flask import flash
# import str as

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shoe.route('/', methods=['GET', 'POST'])
def index():
    # Retrieve all categories from the database
    categories = Category.get_all()

    # Convert category IDs to strings
    for category in categories:
        category['_id'] = str(category['_id'])

    # Retrieve all shoes from the database initially
    shoes = Shoe.get_all()

    # Get cart information
    cart = session.get('cart', [])
    cart_count = len(cart)

    # Get filter parameters from the request
    selected_categories = request.args.getlist('category')
    max_price = request.args.get('max_price', 100)  # Default max price is 100

    # Filter shoes by category ID
    if selected_categories:
        shoes = [shoe for shoe in shoes if str(shoe['category_id']) in selected_categories]

    # Filter shoes by price range
    shoes = [shoe for shoe in shoes if shoe['cost'] <= float(max_price)]

    # Shuffle and get featured shoes
    random.shuffle(shoes)
    featured_shoes = shoes[:3] if len(shoes) >= 3 else shoes

    return render_template('index.html', shoes=shoes, featured_shoes=featured_shoes, cart_count=cart_count, categories=categories)

@shoe.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(shoe.config['UPLOAD_FOLDER'], filename)

import random
@shoe.route('/buyer_dashboard')
@login_required
def buyer_dashboard():
    if session.get("buyer_type") != "buyer":
        flash("Unauthorized access.", "error")
        return redirect(url_for('buyer_login'))
    
    shoes = Shoe.get_all()  # Fetch all shoes
    cart = session.get('cart', [])
    cart_count = len(cart)

    # Fetch variants for all shoes and map them by shoe_id
    shoe_ids = [str(shoe['_id']) for shoe in shoes]
    variants = ShoeVariant.get_by_shoe_ids(shoe_ids)
    variants_by_shoe_id = {}
    for variant in variants:
        shoe_id = variant['shoe_id']
        if shoe_id not in variants_by_shoe_id:
            variants_by_shoe_id[shoe_id] = []
        variants_by_shoe_id[shoe_id].append(variant)

    # Process shoes to include the stock information from variants
    for shoe in shoes:
        shoe_id = str(shoe['_id'])
        shoe_variants = variants_by_shoe_id.get(shoe_id, [])
        in_stock = any(variant.get('stock', 0) > 0 for variant in shoe_variants)
        shoe['in_stock'] = in_stock
        shoe['variants'] = shoe_variants  # Add variants to the shoe data

    return render_template('index.html', session=session, shoes=shoes, cart_count=cart_count)


#     return render_template('buyers/login.html')
@shoe.route('/buyer_login', methods=['GET', 'POST'])
def buyer_login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        
        # Check if buyer exists in the buyer database
        if Buyer.exists_by_email(email):
            buyer = Buyer.get_by_email(email)
            if check_password_hash(buyer['password'], password):
                session["buyer_id"] = str(buyer['_id'])
                session["buyer_type"] = "buyer"
                next_page = session.get('next', url_for('buyer_dashboard'))
                session.pop('next', None)  # Remove 'next' from session after using it
                return redirect(next_page)
            else:
                flash('Invalid credentials', 'error')
        else:
            flash('No such buyer', 'error')

    next_page = request.args.get('next')
    if next_page:
        session['next'] = next_page  # Store the next page URL in the session

    return render_template('buyer/login.html')





@shoe.route('/register_buyer', methods=['GET', 'POST'])
def register_buyer(): 
    try:
        if request.method == 'POST':
            email = request.form.get("email").strip()
            if Buyer.exists_by_email(email):
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
            Buyer.create(data)
            return redirect(url_for('buyer_login'))

        return render_template('buyer/register_buyer.html')
    except Exception as e:
        logger.error(f"Error during buyer registration: {str(e)}")
        return "Internal Server Error", 500
 
@shoe.route('/logout')
def logout():
    try:
        session.clear()  
        session.pop('buyer_id', None)
        session.pop('buyer_type', None)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return "Internal Server Error", 500



 