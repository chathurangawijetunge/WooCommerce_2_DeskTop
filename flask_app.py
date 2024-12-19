
from flask import Flask, render_template, request, redirect, url_for
from woocommerce import API
import tkinter as tk
#from tkinter import messagebox
from urllib.parse import urlparse
import webbrowser

from AGRO_BK import *



# Flask app
app = Flask(__name__)



@app.route('/stock_edit', methods=['GET', 'POST'])
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

            return redirect('/stock_edit')

        return render_template("stock_edit.html", categories=categories, category_names=list(categories.keys()))

    except Exception as e:
        return f"""
            <h1>An error occurred: {e}</h1>
            <button onclick="window.location.reload();">Refresh</button>
            """
#----------------------------------------------------------------------------------------------------------------------------------
@app.route('/price_edit', methods=['GET', 'POST'])
def price_edit():
    try:
        # Fetch products from WooCommerce API
        response = wcapi.get("products", params={"per_page": 100})
        if not response.ok:
            app.logger.error(f"Failed to fetch products: {response.text}")
            return f"Error fetching products: {response.text}"

        # Prepare categories and products for display
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
                    "price": "{:.2f}".format(float(product.get("price", 0))),  # Ensure 2 decimal points
                    "weight": product.get("weight", "N/A"),
                    "id": product.get("id"),
                })

        # Sort products by SKU within each category
        for category_name in categories:
            categories[category_name].sort(key=lambda x: x["sku"])

        if request.method == 'POST':
            # Get the selected category from the form
            selected_category = request.form.get('category_select')

            if selected_category:
                for product in categories.get(selected_category, []):
                    # Get the new price and weight values from the form
                    new_price = request.form.get(f"new_price_{selected_category}_{product['id']}")
                    new_weight = request.form.get(f"new_weight_{selected_category}_{product['id']}")

                    print("FFFFFFFFFFFFFFFFFF SKU:", product["sku"], "Name:", product["name"], "New Price:", new_price, "New Weight:", new_weight)


                    update_data = {}

                    # Update price if the new price is different from the old one
                    if new_price and new_price != str(product["price"]):
                        update_data["regular_price"] = str(new_price) 
                    # Update weight if the new weight is different from the old one
                    if new_weight and new_weight != str(product["weight"]):
                        update_data["weight"] = str(new_weight)

                    if update_data:
                        try:
                            # Send update to WooCommerce API
                            response = wcapi.put(f"products/{product['id']}", update_data)
                            if not response.ok:
                                app.logger.error(f"Failed to update product {product['id']}: {response.text}")
                            else:
                                app.logger.info(f"Product {product['id']} updated with {update_data}.")
                        except Exception as e:
                            app.logger.error(f"Error updating product {product['id']}: {e}")

            # After processing the form, redirect to the same page
            return redirect('/price_edit')

        # Render the price_edit page with categories and products
        return render_template("price_edit.html", categories=categories, category_names=list(categories.keys()))

    except Exception as e:
        # Log and return error if an exception occurs
        app.logger.error(f"An error occurred: {e}")
        return f"""
            <h1>An error occurred: {e}</h1>
            <button onclick="window.location.reload();">Refresh</button>
        """

#----------------------------------------------------------------------------------------------------------------------------------





# Function to run Flask server in a separate thread
def run_server():
    app.run(debug=True, port=8080, use_reloader=False)



# Function to open the web page in the default browser
def stock_edit():
    webbrowser.open("http://127.0.0.1:8080/stock_edit")

def price_edit():
    webbrowser.open("http://127.0.0.1:8080/price_edit")