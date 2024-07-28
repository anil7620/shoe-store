from flask import render_template, request, redirect, url_for, session, jsonify, flash
from shoe import shoe
from shoe.models.user import User
from shoe.models.admin import Admin
from shoe.models.category import Category
from shoe.models.product import Shoe
from shoe.models.order import Order
from shoe.models.ShoeVariant import ShoeVariant
from .decorators import login_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

@shoe.route('/get_all_products')
def get_all_products():
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

@shoe.route('/view_products')
@login_required
def view_products(): 
    products = Shoe.get_all()
    for product in products:
        category = Category.get_by_id(product['category_id'])
        product['category'] = category.get('category_name', 'Unknown Category') if category else 'Unknown Category'
        variants_count = ShoeVariant.count_by_product_id(product['_id'])
        product['variants_count'] = variants_count
        total_in_stock = ShoeVariant.sum_available_stock_by_product_id(product['_id'])
        product['total_in_stock'] = total_in_stock

    return render_template('products/view_products.html', products=products)

@shoe.route('/view_product/<product_id>')
@login_required
def view_product(product_id):
    product = Shoe.get_by_id(product_id)
    category = Category.get_by_id(product['category_id'])
    product['category_name'] = category.get('category_name', 'Unknown Category') if category else 'Unknown Category'
    product_variants = ShoeVariant.get_by_shoe_id(product_id)  # Correct method
    product['variants'] = product_variants
    cart = session.get('cart', [])
    cart_count = len(cart)

    return render_template('products/view_product.html', product=product, cart_count=cart_count)


@shoe.route('/get-variant-info')
def get_variant_info():
    try:
        color = request.args.get('color')
        product_id = request.args.get('productId')
        size = request.args.get('size', None)
        gender = request.args.get('gender', None)
        
        query = {"shoe_id": product_id, "color": color}
        if size:
            query["size"] = size
        if gender:
            query["gender"] = gender
        
        variants = ShoeVariant.collection.find(query)

        if size and gender:
            variant = variants[0] if variants else None
            cost = variant["cost"] if variant else None
            return jsonify(success=True, cost=cost)
        elif size:
            genders = sorted(set([variant["gender"] for variant in variants]))
            return jsonify(success=True, genders=genders)
        else:
            sizes = sorted(set([variant["size"] for variant in variants]))
            return jsonify(success=True, sizes=sizes)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@shoe.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        shoe_name = request.form['shoe_name']
        brand = request.form['brand']
        description = request.form['description']
        created_at = datetime.now()
        status = request.form['status']
        category_id = request.form['category']
        image_url = request.form.get('image_url')
        shipping_methods = request.form.getlist('shipping_method')
        cost = float(request.form['cost'])

        variants = []
        sizes = request.form.getlist('size[]')
        genders = request.form.getlist('gender[]')
        stocks = request.form.getlist('stock[]')
        colors = request.form.getlist('color[]')
        statuses = request.form.getlist('variant_status[]')

        for size, gender, stock, color, variant_status in zip(sizes, genders, stocks, colors, statuses):
            variants.append({
                "size": size,
                "gender": gender,
                "stock": int(stock),
                "color": color,
                "status": variant_status
            })

        data = {
            "shoe_name": shoe_name,
            "brand": brand,
            "description": description,
            "image": image_url,
            "created_at": created_at,
            "status": status,
            "category_id": category_id,
            "cost": cost,
            "variants": variants,
            "shipping_methods": shipping_methods
        }

        product_id = Shoe.create(data)
        if product_id:
            flash("Shoe added successfully", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Shoe not added", "error")
            return redirect(url_for('add_product'))
    else:
        categories = Category.get_all()
        for category in categories:
            category['_id'] = str(category['_id'])
        cart = session.get('cart', [])
        cart_count = len(cart)
        return render_template('products/add_product.html', categories=categories, cart_count=cart_count)


@shoe.route('/edit_product/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if request.method == 'POST':
        shoe_name = request.form['shoe_name']
        brand = request.form['brand']
        description = request.form['description']
        status = request.form['status']
        category_id = request.form['category']
        image_url = request.form.get('image_url')
        shipping_methods = request.form.getlist('shipping_method')
        cost = float(request.form['cost'])

        variants = []
        sizes = request.form.getlist('size[]')
        genders = request.form.getlist('gender[]')
        stocks = request.form.getlist('stock[]')
        colors = request.form.getlist('color[]')
        statuses = request.form.getlist('variant_status[]')

        for size, gender, stock, color, variant_status in zip(sizes, genders, stocks, colors, statuses):
            variants.append({
                "size": size,
                "gender": gender,
                "stock": int(stock),
                "color": color,
                "status": variant_status
            })

        data = {
            "shoe_name": shoe_name,
            "brand": brand,
            "description": description,
            "image": image_url,
            "status": status,
            "category_id": category_id,
            "cost": cost,
            "variants": variants,
            "shipping_methods": shipping_methods
        }

        # Update the shoe details
        shoe_updated = Shoe.update(product_id, data)

        if shoe_updated:
            flash("Shoe updated successfully", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Shoe not updated", "error")
            return redirect(url_for('edit_product', product_id=product_id))
    else:
        shoe = Shoe.get_by_id(product_id)
        categories = Category.get_all()
        for category in categories:
            category['_id'] = str(category['_id'])
        cart = session.get('cart', [])
        cart_count = len(cart)
        return render_template('products/edit_product.html', shoe=shoe, categories=categories, cart_count=cart_count)


@shoe.route('/delete_product/<product_id>', methods=['GET'])
@login_required
def delete_product(product_id):
    try:
        print('====',product_id)
        variants_deleted = ShoeVariant.delete_many({"shoe_id": product_id})

        # Delete the shoe itself
        product_deleted = Shoe.delete(product_id)

        if product_deleted and variants_deleted:
            flash("Shoe and its variants deleted successfully", "success")
        else:
            flash("Shoe or some variants could not be deleted", "error")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
    
    return redirect(url_for('admin_dashboard'))
@shoe.route('/view_users')
@login_required
def view_users():
    users = User.get_all()
    return render_template('users/view_users.html', users=users)
