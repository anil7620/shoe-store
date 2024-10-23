from flask import render_template, request, redirect, url_for, session, jsonify, flash
from shoe import shoe
from shoe.models.buyer import Buyer
from shoe.models.admin import Admin
from shoe.models.category import Category
from shoe.models.shoe import Shoe
from shoe.models.order import Order
from shoe.models.ShoeVariant import ShoeVariant
from .decorators import login_required
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json

@shoe.route('/get_all_shoes')
def get_all_shoes():
    shoes = Shoe.get_all()
    cart = session.get('cart', [])
    cart_count = len(cart)
    shoe_ids = [str(shoe['_id']) for shoe in shoes]
    shoe_variants = ShoeVariant.get_by_shoe_ids(shoe_ids)

    # Organize variants by shoe_id
    variants_by_shoe_id = {}
    for variant in shoe_variants:
        shoe_id = variant['shoe_id']
        if shoe_id not in variants_by_shoe_id:
            variants_by_shoe_id[shoe_id] = []
        variants_by_shoe_id[shoe_id].append(variant)

    # Add variants to shoes
    for shoe in shoes:
        shoe_id = str(shoe['_id'])
        shoe['variants'] = variants_by_shoe_id.get(shoe_id, [])
        shoe['in_stock'] = any(variant['stock'] > 0 for variant in shoe['variants'])


    return render_template('index.html', shoes=shoes, cart_count=cart_count)

@shoe.route('/view_shoes')
@login_required
def view_shoes(): 
    shoes = Shoe.get_all()
    for shoe in shoes:
        category = Category.get_by_id(shoe['category_id'])
        shoe['category'] = category.get('category_name', 'Unknown Category') if category else 'Unknown Category'
        variants_count = ShoeVariant.count_by_shoe_id(shoe['_id'])
        shoe['variants_count'] = variants_count
        total_in_stock = ShoeVariant.sum_available_stock_by_shoe_id(shoe['_id'])
        shoe['total_in_stock'] = total_in_stock

    return render_template('shoes/view_shoes.html', shoes=shoes)

@shoe.route('/view_shoe/<shoe_id>')
@login_required
def view_shoe(shoe_id):
    # Buyer-specific logic
    shoe = Shoe.get_by_id(shoe_id)
    category = Category.get_by_id(shoe['category_id'])
    shoe['category_name'] = category.get('category_name', 'Unknown Category') if category else 'Unknown Category'
    shoe_variants = ShoeVariant.get_by_shoe_id(shoe_id)
    shoe['variants'] = shoe_variants
    cart = session.get('cart', [])
    cart_count = len(cart)

    return render_template('shoes/view_shoe.html', shoe=shoe, cart_count=cart_count)


@shoe.route('/get-variant-info')
def get_variant_info():
    try:
        color = request.args.get('color')
        shoe_id = request.args.get('shoeId')
        size = request.args.get('size', None)
        gender = request.args.get('gender', None)
        
        query = {"shoe_id": shoe_id, "color": color}
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

@shoe.route('/add_shoe', methods=['GET', 'POST'])
@login_required
def add_shoe():
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

        shoe_id = Shoe.create(data)
        if shoe_id:
            flash("Shoe added successfully", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Shoe not added", "error")
            return redirect(url_for('add_shoe'))
    else:
        categories = Category.get_all()
        for category in categories:
            category['_id'] = str(category['_id'])
        cart = session.get('cart', [])
        cart_count = len(cart)
        return render_template('shoes/add_shoe.html', categories=categories, cart_count=cart_count)


@shoe.route('/edit_shoe/<shoe_id>', methods=['GET', 'POST'])
@login_required
def edit_shoe(shoe_id):
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
        shoe_updated = Shoe.update(shoe_id, data)

        if shoe_updated:
            flash("Shoe updated successfully", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Shoe not updated", "error")
            return redirect(url_for('edit_shoe', shoe_id=shoe_id))
    else:
        shoe = Shoe.get_by_id(shoe_id)
        categories = Category.get_all()
        for category in categories:
            category['_id'] = str(category['_id'])
        cart = session.get('cart', [])
        cart_count = len(cart)
        return render_template('shoes/edit_shoe.html', shoe=shoe, categories=categories, cart_count=cart_count)


@shoe.route('/delete_shoe/<shoe_id>', methods=['GET'])
@login_required
def delete_shoe(shoe_id):
    try:
        print('====',shoe_id)
        variants_deleted = ShoeVariant.delete_many({"shoe_id": shoe_id})

        # Delete the shoe itself
        shoe_deleted = Shoe.delete(shoe_id)

        if shoe_deleted and variants_deleted:
            flash("Shoe and its variants deleted successfully", "success")
        else:
            flash("Shoe or some variants could not be deleted", "error")
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
    
    return redirect(url_for('admin_dashboard'))
@shoe.route('/view_buyers')
@login_required
def view_buyers():
    buyers = Buyer.get_all()
    return render_template('buyers/view_buyers.html', buyers=buyers)
