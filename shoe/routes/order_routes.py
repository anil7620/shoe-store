from flask import render_template, request, redirect, url_for, session, jsonify, flash
from shoe import shoe
from shoe.models.buyer import Buyer
from shoe.models.admin import Admin
from shoe.models.category import Category
from shoe.models.shoe import Shoe
from bson import ObjectId
from .decorators import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from shoe.models.ShoeVariant import ShoeVariant
from shoe.models.order import Order
from datetime import datetime
from shoe.models.cart import Cart
import os 


@shoe.route('/add_to_cart/<shoe_id>', methods=['POST'])
def add_to_cart(shoe_id):
    buyer_id = session.get('buyer_id')
    if not buyer_id:
        flash('You must be logged in to add.', 'error')
        return redirect(url_for('buyer_login'))

    color = request.form.get('color')
    size = request.form.get('size')
    gender = request.form.get('gender')
    quantity = int(request.form.get('quantity', 1))

    if not color or not size or not gender:
        flash('You must select a color, size, and gender.', 'error')
        return redirect(url_for('view_shoe', shoe_id=shoe_id))

    variant = ShoeVariant.find_one({
        'shoe_id': str(shoe_id),
        'color': color,
        'size': size,
        'gender': gender
    })

    print(f"Variant for shoe {shoe_id}: {variant}")  # Debugging line

    if not variant or variant['stock'] < quantity:
        flash('Selected variant is out of stock or insufficient stock.', 'error')
        return redirect(url_for('view_shoe', shoe_id=shoe_id))

    cart_data = Cart.get_by_buyer_id(buyer_id)
    if not cart_data:
        cart_data = {"buyer_id": ObjectId(buyer_id), "items": []}

    cart_items = cart_data.get("items", [])
    print("==cart_items===")
    print(cart_items)
    print("==cart_entry===")

    cart_entry = next((item for item in cart_items if 'variant_id' in item and item['variant_id'] == str(variant['_id'])), None)
    print(cart_entry)
    if not cart_entry:
        cart_entry = {'shoe_id': shoe_id, 'variant_id': str(variant['_id']), 'quantity': 0}
        cart_items.append(cart_entry)

    if variant['stock'] < (cart_entry['quantity'] + quantity):
        flash('Adding this shoe will exceed the available stock.', 'error')
        return redirect(url_for('view_shoe', shoe_id=shoe_id))

    cart_entry['quantity'] += quantity
    Cart.save_cart(buyer_id, cart_items)
    flash('Shoe added to cart', 'success')
    print(cart_items)
    print("shoe added to cart")
    return redirect(url_for('view_cart'))



# @shoe.route('/remove_from_cart/<shoe_id>', methods=['POST'])
# def remove_from_cart(shoe_id):
#     buyer_id = session.get('buyer_id')
#     if not buyer_id:
#         flash('You must be logged in to remove items from cart.', 'error')
#         return redirect(url_for('buyer_login'))

#     cart_data = Cart.get_by_buyer_id(buyer_id)
#     if cart_data:
#         cart_items = [item for item in cart_data['items'] if item['shoe_id'] != shoe_id]
#         Cart.save_cart(buyer_id, cart_items)

#     flash('Shoe removed from cart', 'success')
#     return redirect(url_for('view_cart'))
# @shoe.route('/increase_quantity/<shoe_id>', methods=['POST'])
# def increase_quantity(shoe_id):
#     buyer_id = session.get('buyer_id')
#     if not buyer_id:
#         flash('You must be logged in to increase quantity.', 'error')
#         return redirect(url_for('buyer_login'))

#     cart_data = Cart.get_by_buyer_id(buyer_id)
#     if not cart_data:
#         cart_data = {"buyer_id": ObjectId(buyer_id), "items": []}

#     cart_items = cart_data.get("items", [])
#     shoe = Shoe.get_by_id(shoe_id)
#     if not shoe:
#         flash('Shoe not found.', 'error')
#         return redirect(url_for('view_cart'))

#     cart_entry = next((item for item in cart_items if item['shoe_id'] == shoe_id), None)
#     if cart_entry:
#         current_quantity = cart_entry.get('quantity', 0)
#         variants = ShoeVariant.get_by_shoe_id(shoe_id)
#         if not variants:
#             flash('No variants found for this shoe.', 'error')
#             return redirect(url_for('view_cart'))
        
#         total_stock = sum(variant['stock'] for variant in variants if variant['stock'] > 0)
#         if current_quantity + 1 > total_stock:
#             flash('Insufficient stock for this shoe.', 'error')
#             return redirect(url_for('view_cart'))
#         cart_entry['quantity'] += 1

#     Cart.save_cart(buyer_id, cart_items)
#     return redirect(url_for('view_cart'))


# @shoe.route('/decrease_quantity/<shoe_id>', methods=['POST'])
# def decrease_quantity(shoe_id):
#     buyer_id = session.get('buyer_id')
#     if not buyer_id:
#         flash('You must be logged in to decrease quantity.', 'error')
#         return redirect(url_for('buyer_login'))

#     cart_data = Cart.get_by_buyer_id(buyer_id)
#     if cart_data:
#         cart_items = cart_data.get("items", [])
#         cart_entry = next((item for item in cart_items if item['shoe_id'] == shoe_id), None)
#         if cart_entry:
#             if cart_entry['quantity'] > 1:
#                 cart_entry['quantity'] -= 1
#             else:
#                 cart_items.remove(cart_entry)
#         Cart.save_cart(buyer_id, cart_items)

#     return redirect(url_for('view_cart'))

@shoe.route('/increase_quantity/<variant_id>', methods=['POST'])
def increase_quantity(variant_id):
    buyer_id = session.get('buyer_id')
    if not buyer_id:
        flash('You must be logged in to increase quantity.', 'error')
        return redirect(url_for('buyer_login'))

    cart_data = Cart.get_by_buyer_id(buyer_id)
    if not cart_data:
        cart_data = {"buyer_id": ObjectId(buyer_id), "items": []}

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

    Cart.save_cart(buyer_id, cart_items)
    return redirect(url_for('view_cart'))

@shoe.route('/decrease_quantity/<variant_id>', methods=['POST'])
def decrease_quantity(variant_id):
    buyer_id = session.get('buyer_id')
    if not buyer_id:
        flash('You must be logged in to decrease quantity.', 'error')
        return redirect(url_for('buyer_login'))

    cart_data = Cart.get_by_buyer_id(buyer_id)
    if cart_data:
        cart_items = cart_data.get("items", [])
        cart_entry = next((item for item in cart_items if item['variant_id'] == variant_id), None)
        if cart_entry:
            if cart_entry['quantity'] > 1:
                cart_entry['quantity'] -= 1
            else:
                cart_items.remove(cart_entry)
        Cart.save_cart(buyer_id, cart_items)

    return redirect(url_for('view_cart'))

@shoe.route('/cart')
def view_cart():
    buyer_id = session.get('buyer_id')
    if not buyer_id:
        flash('You must be logged in to view the cart.', 'error')
        return redirect(url_for('buyer_login'))
    print("in /cart")
    cart_data = Cart.get_by_buyer_id(buyer_id)
    print(cart_data)
    items = cart_data['items'] if cart_data else []
    print(items)

    shoes = []
    total_cost = 0
    tax_rate = 0.10  # Assuming a tax rate of 10%

    for item in items:
        shoe = Shoe.get_by_id(item['shoe_id'])
        variant = ShoeVariant.get_by_id(item['variant_id'])  # Fetch the variant

        if shoe and variant:
            quantity = item['quantity']
            shoe['quantity'] = quantity
            shoe_total = float(shoe['cost']) * int(quantity)  # Use shoe cost

            total_cost += float(shoe_total)
            shoes.append({
                'shoe': shoe,
                'variant': variant,  # Include variant in the shoe
                'shoe_total': shoe_total, 
            })

    total_tax = round(total_cost * tax_rate, 2)
    total_payable = round(total_cost + total_tax, 2)
    print(shoes)
    return render_template('orders/cart.html', shoes=shoes, cart_count=len(items), total_cost=total_cost, total_tax=total_tax, total_payable=total_payable)



@shoe.route('/remove_from_cart/<variant_id>', methods=['POST'])
def remove_from_cart(variant_id):
    buyer_id = session.get('buyer_id')
    if not buyer_id:
        flash('You must be logged in to remove items from the cart.', 'error')
        return redirect(url_for('buyer_login'))

    cart_data = Cart.get_by_buyer_id(buyer_id)
    if cart_data:
        cart_items = cart_data.get("items", [])
        cart_entry = next((item for item in cart_items if item['variant_id'] == variant_id), None)
        if cart_entry:
            cart_items.remove(cart_entry)
        Cart.save_cart(buyer_id, cart_items)

    return redirect(url_for('view_cart'))


@shoe.route('/view_buyer_orders')
@login_required
def view_buyer_orders():
    buyer_id = session.get("buyer_id")
    orders = Order.get_by_buyer_id(ObjectId(buyer_id))
    print(orders)
    cart = session.get('cart', [])
    cart_count = len(cart)
    
    for order in orders:
        cart_items = order['shoes']
        shoe_details = []
        for item in cart_items:
            shoe_data = item.get('shoe')
            shoe_id = shoe_data.get('_id')
            quantity = item.get('quantity') 
            variant = item.get('variant')
            shoe = Shoe.get_by_id(shoe_id)
            if shoe:
                shoe_details.append({
                    "shoe_name": shoe['shoe_name'],
                    "quantity": quantity,
                    "variant_color": variant['color'],
                    "variant_size": variant['size'],
                    "variant_gender": variant['gender'],
                })
        order['shoe_details'] = shoe_details 

    return render_template('orders/view_buyer_orders.html', orders=orders, cart_count=cart_count)
