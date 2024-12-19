
from flask import Flask, render_template, request, redirect, url_for
from woocommerce import API
import tkinter as tk
#from tkinter import messagebox
from urllib.parse import urlparse
import webbrowser

from AGRO_BK import *



# Flask app
app = Flask(__name__)



@app.route('/', methods=['GET', 'POST'])
def display_products():
    try:
        response = wcapi.get("products", params={"per_page": 100})
        if not response.ok:
            app.logger.error(f"Failed to fetch products: {response.text}")
            return f"Error fetching products: {response.text}"

        products = response.json()
        categories = {}
        for product in products:
            for category in product.get("categories", []):
                category_name = category["name"]
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append({
                    "sku": product.get("sku", "N/A"),
                    "name": product.get("name", "N/A"),
                    "stock": product.get("stock_quantity", "N/A"),
                    "id": product.get("id"),
                })

        for category_name in categories:
            categories[category_name].sort(key=lambda x: x["sku"])

        if request.method == 'POST':
            selected_category = request.form.get('category_select')

            if selected_category:
                for product in categories.get(selected_category, []):
                    new_stock = request.form.get(f"new_stock_{selected_category}_{product['id']}")
                    if new_stock and new_stock != str(product['stock']):
                        try:
                            data = {"stock_quantity": int(new_stock)}
                            response = wcapi.put(f"products/{product['id']}", data)
                            if not response.ok:
                                app.logger.error(f"Failed to update product {product['id']}: {response.text}")
                            else:
                                app.logger.info(f"Product {product['id']} updated to {new_stock} stock.")
                        except Exception as e:
                            app.logger.error(f"Error updating product {product['id']}: {e}")

            return redirect('/')

        return render_template("products.html", categories=categories, category_names=list(categories.keys()))

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return f"An error occurred: {e}"

# Function to run Flask server in a separate thread
def run_server():
    app.run(debug=True, port=8080, use_reloader=False)



# Function to open the web page in the default browser
def open_home_page():
    webbrowser.open("http://127.0.0.1:8080")