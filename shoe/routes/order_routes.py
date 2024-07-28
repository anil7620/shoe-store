from flask import render_template, request, redirect, url_for, session, jsonify, flash
from shoe import shoe
from shoe.models.user import User
from shoe.models.admin import Admin
from shoe.models.category import Category
from shoe.models.product import Shoe
from bson import ObjectId
from .decorators import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from shoe.models.ShoeVariant import ShoeVariant
from shoe.models.order import Order
from datetime import datetime
from shoe.models.cart import Cart
import os 


@shoe.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to add.', 'error')
        return redirect(url_for('user_login'))

    color = request.form.get('color')
    size = request.form.get('size')
    gender = request.form.get('gender')
    quantity = int(request.form.get('quantity', 1))

    if not color or not size or not gender:
        flash('You must select a color, size, and gender.', 'error')
        return redirect(url_for('view_product', product_id=product_id))

    variant = ShoeVariant.find_one({
        'shoe_id': str(product_id),
        'color': color,
        'size': size,
        'gender': gender
    })

    print(f"Variant for product {product_id}: {variant}")  # Debugging line

    if not variant or variant['stock'] < quantity:
        flash('Selected variant is out of stock or insufficient stock.', 'error')
        return redirect(url_for('view_product', product_id=product_id))

    cart_data = Cart.get_by_user_id(user_id)
    if not cart_data:
        cart_data = {"user_id": ObjectId(user_id), "items": []}

    cart_items = cart_data.get("items", [])
    print("==cart_items===")
    print(cart_items)
    print("==cart_entry===")

    cart_entry = next((item for item in cart_items if 'variant_id' in item and item['variant_id'] == str(variant['_id'])), None)
    print(cart_entry)
    if not cart_entry:
        cart_entry = {'product_id': product_id, 'variant_id': str(variant['_id']), 'quantity': 0}
        cart_items.append(cart_entry)

    if variant['stock'] < (cart_entry['quantity'] + quantity):
        flash('Adding this product will exceed the available stock.', 'error')
        return redirect(url_for('view_product', product_id=product_id))

    cart_entry['quantity'] += quantity
    Cart.save_cart(user_id, cart_items)
    flash('Shoe added to cart', 'success')
    print(cart_items)
    print("shoe added to cart")
    return redirect(url_for('view_cart'))



# @shoe.route('/remove_from_cart/<product_id>', methods=['POST'])
# def remove_from_cart(product_id):
#     user_id = session.get('user_id')
#     if not user_id:
#         flash('You must be logged in to remove items from cart.', 'error')
#         return redirect(url_for('user_login'))

#     cart_data = Cart.get_by_user_id(user_id)
#     if cart_data:
#         cart_items = [item for item in cart_data['items'] if item['product_id'] != product_id]
#         Cart.save_cart(user_id, cart_items)

#     flash('Shoe removed from cart', 'success')
#     return redirect(url_for('view_cart'))
# @shoe.route('/increase_quantity/<product_id>', methods=['POST'])
# def increase_quantity(product_id):
#     user_id = session.get('user_id')
#     if not user_id:
#         flash('You must be logged in to increase quantity.', 'error')
#         return redirect(url_for('user_login'))

#     cart_data = Cart.get_by_user_id(user_id)
#     if not cart_data:
#         cart_data = {"user_id": ObjectId(user_id), "items": []}

#     cart_items = cart_data.get("items", [])
#     product = Shoe.get_by_id(product_id)
#     if not product:
#         flash('Product not found.', 'error')
#         return redirect(url_for('view_cart'))

#     cart_entry = next((item for item in cart_items if item['product_id'] == product_id), None)
#     if cart_entry:
#         current_quantity = cart_entry.get('quantity', 0)
#         variants = ShoeVariant.get_by_shoe_id(product_id)
#         if not variants:
#             flash('No variants found for this product.', 'error')
#             return redirect(url_for('view_cart'))
        
#         total_stock = sum(variant['stock'] for variant in variants if variant['stock'] > 0)
#         if current_quantity + 1 > total_stock:
#             flash('Insufficient stock for this product.', 'error')
#             return redirect(url_for('view_cart'))
#         cart_entry['quantity'] += 1

#     Cart.save_cart(user_id, cart_items)
#     return redirect(url_for('view_cart'))


# @shoe.route('/decrease_quantity/<product_id>', methods=['POST'])
# def decrease_quantity(product_id):
#     user_id = session.get('user_id')
#     if not user_id:
#         flash('You must be logged in to decrease quantity.', 'error')
#         return redirect(url_for('user_login'))

#     cart_data = Cart.get_by_user_id(user_id)
#     if cart_data:
#         cart_items = cart_data.get("items", [])
#         cart_entry = next((item for item in cart_items if item['product_id'] == product_id), None)
#         if cart_entry:
#             if cart_entry['quantity'] > 1:
#                 cart_entry['quantity'] -= 1
#             else:
#                 cart_items.remove(cart_entry)
#         Cart.save_cart(user_id, cart_items)

#     return redirect(url_for('view_cart'))

@shoe.route('/increase_quantity/<variant_id>', methods=['POST'])
def increase_quantity(variant_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to increase quantity.', 'error')
        return redirect(url_for('user_login'))

    cart_data = Cart.get_by_user_id(user_id)
    if not cart_data:
        cart_data = {"user_id": ObjectId(user_id), "items": []}

    cart_items = cart_data.get("items", [])
    variant = ShoeVariant.get_by_id(variant_id)
    if not variant:
        flash('Variant not found.', 'error')
        return redirect(url_for('view_cart'))

    cart_entry = next((item for item in cart_items if item['variant_id'] == variant_id), None)
    if cart_entry:
        current_quantity = cart_entry.get('quantity', 0)
        total_stock = variant['stock']
        if current_quantity + 1 > total_stock:
            flash('Insufficient stock for this variant.', 'error')
            return redirect(url_for('view_cart'))
        cart_entry['quantity'] += 1
    else:
        cart_items.append({"variant_id": variant_id, "quantity": 1})

    Cart.save_cart(user_id, cart_items)
    return redirect(url_for('view_cart'))

@shoe.route('/decrease_quantity/<variant_id>', methods=['POST'])
def decrease_quantity(variant_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to decrease quantity.', 'error')
        return redirect(url_for('user_login'))

    cart_data = Cart.get_by_user_id(user_id)
    if cart_data:
        cart_items = cart_data.get("items", [])
        cart_entry = next((item for item in cart_items if item['variant_id'] == variant_id), None)
        if cart_entry:
            if cart_entry['quantity'] > 1:
                cart_entry['quantity'] -= 1
            else:
                cart_items.remove(cart_entry)
        Cart.save_cart(user_id, cart_items)

    return redirect(url_for('view_cart'))

@shoe.route('/cart')
def view_cart():
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to view the cart.', 'error')
        return redirect(url_for('user_login'))
    print("in /cart")
    cart_data = Cart.get_by_user_id(user_id)
    print(cart_data)
    items = cart_data['items'] if cart_data else []
    print(items)

    products = []
    total_cost = 0
    tax_rate = 0.10  # Assuming a tax rate of 10%

    for item in items:
        product = Shoe.get_by_id(item['product_id'])
        variant = ShoeVariant.get_by_id(item['variant_id'])  # Fetch the variant

        if product and variant:
            quantity = item['quantity']
            product['quantity'] = quantity
            product_total = float(product['cost']) * int(quantity)  # Use product cost

            total_cost += float(product_total)
            products.append({
                'product': product,
                'variant': variant,  # Include variant in the product
                'product_total': product_total, 
            })

    total_tax = round(total_cost * tax_rate, 2)
    total_payable = round(total_cost + total_tax, 2)
    print(products)
    return render_template('orders/cart.html', products=products, cart_count=len(items), total_cost=total_cost, total_tax=total_tax, total_payable=total_payable)
@shoe.route('/remove_from_cart/<variant_id>', methods=['POST'])
def remove_from_cart(variant_id):
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to remove items from the cart.', 'error')
        return redirect(url_for('user_login'))

    cart_data = Cart.get_by_user_id(user_id)
    if cart_data:
        cart_items = cart_data.get("items", [])
        cart_entry = next((item for item in cart_items if item['variant_id'] == variant_id), None)
        if cart_entry:
            cart_items.remove(cart_entry)
        Cart.save_cart(user_id, cart_items)

    return redirect(url_for('view_cart'))


@shoe.route('/view_user_orders')
@login_required
def view_user_orders():
    user_id = session.get("user_id")
    orders = Order.get_by_user_id(ObjectId(user_id))
    print(orders)
    cart = session.get('cart', [])
    cart_count = len(cart)
    
    for order in orders:
        cart_items = order['products']
        product_details = []
        for item in cart_items:
            product_data = item.get('product')
            product_id = product_data.get('_id')
            quantity = item.get('quantity') 
            variant = item.get('variant')
            product = Shoe.get_by_id(product_id)
            if product:
                product_details.append({
                    "shoe_name": product['shoe_name'],
                    "quantity": quantity,
                    "variant_color": variant['color'],
                    "variant_size": variant['size'],
                    "variant_gender": variant['gender'],
                })
        order['product_details'] = product_details 

    return render_template('orders/view_user_orders.html', orders=orders, cart_count=cart_count)
