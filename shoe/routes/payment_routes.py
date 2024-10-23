# shoe/profile_routes.py

from flask import render_template, request, redirect, url_for, session, flash
from shoe import shoe
from shoe.models.buyer import Buyer
from shoe.models.admin import Admin
from shoe.models.category import Category
from shoe.models.order import Order
from shoe.models.shoe import Shoe
from shoe.models.payment import Payment
from shoe.models.ShoeVariant import ShoeVariant
from .decorators import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from bson import ObjectId
from shoe.models.cart import Cart

@shoe.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    buyer_id = session.get("buyer_id")
    if not buyer_id:
        flash('You must be logged in to proceed with checkout.', 'error')
        return redirect(url_for('buyer_login'))

    if request.method == 'POST':
        cart_data = Cart.get_by_buyer_id(buyer_id)
        if not cart_data or not cart_data.get('items'):
            flash('Your cart is empty', 'error')
            return redirect(url_for('view_cart'))

        cart_items = cart_data['items']

        # Process each item in the cart
        total_cost = 0.0
        shoes_details = []
        for item in cart_items:
            shoe_id = item['shoe_id']
            shoe = Shoe.get_by_id(shoe_id)
            if not shoe:
                continue

            quantity = int(request.form.get(f'quantity_{shoe_id}', item['quantity']))
            variant_id = item.get('variant_id')
            if not variant_id:
                flash(f'Variant ID missing for {shoe["shoe_name"]}.', 'error')
                continue

            variant = ShoeVariant.get_by_id(variant_id)
            if not variant:
                flash(f'Variant for {shoe["shoe_name"]} not found.', 'error')
                continue

            if variant['stock'] < quantity:
                flash(f'Insufficient stock for {shoe["shoe_name"]} (Size: {variant["size"]}, Color: {variant["color"]}).', 'error')
                return redirect(url_for('view_cart'))

            shoe_total = float(shoe['cost']) * quantity
            total_cost += shoe_total
            shoes_details.append({
                'shoe': shoe,
                'variant': variant,
                'quantity': quantity,
                'subtotal': shoe_total
            })

        if not shoes_details:
            flash('No valid shoes to checkout.', 'error')
            return redirect(url_for('view_cart'))

        # Calculate the total with tax
        total_cost += total_cost * 0.10

        # Get the selected shipping method
        shipping_method = request.form.get('shipping_method')
        if not shipping_method:
            flash('Please select a shipping method.', 'error')
            return redirect(url_for('checkout'))

        # Save the order
        order_data = {
            "buyer_id": ObjectId(buyer_id),
            "shoes": shoes_details,
            "total": total_cost,
            "shipping_method": shipping_method,
            "status": "pending",
            "created_at": datetime.now(),
        }
        order = Order.save(order_data)
        order_id = order.inserted_id

        # Save the payment
        payment_data = {
            "buyer_id": ObjectId(buyer_id),
            "order_id": order_id,
            "total": total_cost,
            "card_number": request.form.get("card_number"),
            "expiry_date": request.form.get("expiry_date"),
            "cvv": request.form.get("cvv"),
            "name_on_card": request.form.get("name_on_card"),
            "status": "paid",
            "created_at": datetime.now(),
        }
        Payment.save(payment_data)

        # Update order status to paid
        Order.update(order_id, {"status": "paid", "payment_id": payment_data['_id']})

        # Decrease the quantity in stock for each shoe variant
        for shoe_detail in shoes_details:
            variant = shoe_detail['variant']
            quantity_purchased = shoe_detail['quantity']
            new_stock = max(variant['stock'] - quantity_purchased, 0)  # Ensure stock doesn't go negative
            ShoeVariant.update(variant['_id'], {"stock": new_stock})

        # Clear the cart after checkout
        Cart.clear_cart(buyer_id)
        flash("Payment successful. Check your email for confirmation.", "success")
        return redirect(url_for('buyer_dashboard'))

    # Prepare display of cart items for GET request
    cart_data = Cart.get_by_buyer_id(buyer_id)
    cart_items = cart_data['items'] if cart_data else []

    shoes = []
    total_cost = 0.0
    for item in cart_items:
        shoe_id = item['shoe_id']
        shoe = Shoe.get_by_id(shoe_id)
        if shoe:
            quantity = item['quantity']
            variant_id = item.get('variant_id')
            if not variant_id:
                continue

            variant = ShoeVariant.get_by_id(variant_id)
            if not variant:
                continue

            shoe_total = float(shoe['cost']) * quantity
            total_cost += shoe_total
            shoes.append({
                'shoe': shoe,
                'variant': variant,
                'quantity': quantity,
                'subtotal': shoe_total
            })

    total_tax = round(total_cost * 0.10, 2)
    total_payable = round(total_cost + total_tax, 2)
    cart = session.get('cart', {})
    cart_count = len(cart)
    return render_template('orders/checkout.html', shoes=shoes, total_cost=total_cost, total_tax=total_tax, total_payable=total_payable, cart_count=cart_count)
