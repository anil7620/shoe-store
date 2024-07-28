# shoe/profile_routes.py

from flask import render_template, request, redirect, url_for, session
from shoe import shoe 
from shoe.models.user import User
from shoe.models.admin import Admin
from shoe.models.category import Category
from .decorators import login_required
from flask import flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@shoe.route('/view_categories')
@login_required
def view_categories(): 

    categories = Category.get_all() 
    return render_template('admin/view_categories.html', categories=categories) 



@shoe.route('/add_category', methods=['GET', 'POST'])
def add_category():
    try:
        if request.method == 'POST':
            # Retrieve data from the form
            category_name = request.form.get("category_name").strip()
            description = request.form.get("description").strip()
            status = request.form.get("status").strip()

          
            # Create a dictionary with the category data
            category_data = {
                "category_name": category_name,
                "description": description,
                "status": status,
                "created_at": datetime.utcnow()  # You may need to adjust the timestamp based on your requirements
            }

            # Call the Category model method to create the category
            Category.create(category_data)
            flash("Category added successfully.")
            # Redirect to a success page or a different route
            return redirect(url_for('view_categories'))

        elif request.method == 'GET':
            # Render the form for adding a category
            return render_template('admin/add_category.html')

    except Exception as e:
        flash("An error occurred while adding the category.")
        return "An error occurred while adding the category.", 500


@shoe.route('/edit_category/<category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    try:
        if request.method == 'POST': 
            category_name = request.form.get("category_name").strip()
            description = request.form.get("description").strip()
            status = request.form.get("status").strip()  

            # Create a dictionary with the category data
            category_data = {
                "category_name": category_name,
                "description": description,
                "status": status, 
                "updated_at": datetime.utcnow()  # You may need to adjust the timestamp based on your requirements
            }

            # Call the Category model method to update the category
            Category.update(category_id, category_data)
            flash("Category updated successfully.")
            # Redirect to a success page or a different route
            return redirect(url_for('view_categories'))  # Replace 'admin_dashboard' with the route you want to redirect to after updating the category

        elif request.method == 'GET': 
            category = Category.get_by_id(category_id) 
            return render_template('admin/edit_category.html', category=category)

    except Exception as e: 
        flash("An error occurred while editing the category.")
        return "An error occurred while editing the category.", 500
    

@shoe.route('/delete_category/<category_id>', methods=['GET', 'POST'])
def delete_category(category_id):
    try:
        Category.delete(category_id)
        flash("Category deleted successfully.") 
        return redirect(url_for('view_categories'))  
    except Exception as e: 
        flash("An error occurred while deleting the category.")
        return "An error occurred while deleting the category.", 500