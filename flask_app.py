
from flask import Flask, render_template, request, redirect, url_for,jsonify
from woocommerce import API
import tkinter as tk
#from tkinter import messagebox
from urllib.parse import urlparse
import webbrowser

from AGRO_BK import *



# Flask app
app = Flask(__name__)

def page_reload(e):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f8d7da;
            }}
            .error-box {{
                background-color: #ffffff;
                border: 2px solid #f5c6cb;
                color: #721c24;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            .countdown {{
                font-weight: bold;
                font-size: 1.5em;
            }}
        </style>
    </head>
    <body>
        <div class="error-box">
            <h3>An error occurred: {e}</h3>
            <p>The page will refresh automatically in <span class="countdown" id="countdown">5</span> seconds.</p>
            <button onclick="window.location.reload();">Refresh Now</button>
        </div>
        <script>
            let countdown = 5;
            const countdownElement = document.getElementById('countdown');

            const timer = setInterval(() => {{
                countdown--;
                countdownElement.textContent = countdown;
                if (countdown <= 0) {{
                    clearInterval(timer);
                    window.location.reload();
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    """



@app.route('/stock_edit', methods=['GET', 'POST'])
def display_products():
    try:
        products = []
        page = 1  # Start at the first page
        per_page = 100  # Set the maximum allowed per_page (100 is the max for WooCommerce)

        # Loop through pages until no products are returned
        while True:
            # Fetch a page of products from the WooCommerce API
            response = wcapi.get("products", params={"per_page": per_page, "page": page})
            if not response.ok:
                app.logger.error(f"Failed to fetch products: {response.text}")
                return f"Error fetching products: {response.text}", 500

            page_products = response.json()  # Get the list of products from the response
            # Break the loop if no products are returned (i.e., last page)
            if not page_products:
                break
            products.extend(page_products)  # Add the fetched products to the list
            page += 1  # Move to the next page

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
        return page_reload(e)
#----------------------------------------------------------------------------------------------------------------------------------


@app.route('/price_edit', methods=['GET', 'POST'])
def price_edit():
    try:
        products = []
        page = 1  # Start at the first page
        per_page = 100  # Set the maximum allowed per_page (100 is the max for WooCommerce)

        # Loop through pages until no products are returned
        while True:
            # Fetch a page of products from the WooCommerce API
            response = wcapi.get("products", params={"per_page": per_page, "page": page})
            if not response.ok:
                app.logger.error(f"Failed to fetch products: {response.text}")
                return f"Error fetching products: {response.text}", 500

            page_products = response.json()  # Get the list of products from the response

            # Break the loop if no products are returned (i.e., last page)
            if not page_products:
                break

            products.extend(page_products)  # Add the fetched products to the list
            page += 1  # Move to the next page

        categories = {}
        for product in products:
            # Organize products by category
            for category in product.get("categories", []):
                category_name = category["name"]
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append({
                    "sku": product.get("sku", "N/A"),
                    "name": product.get("name", "N/A"),
                    "price": "{:.2f}".format(float(product.get("price", 0))),
                    "id": product.get("id"),
                })

        # Sort products by SKU within each category
        for category_name in categories:
            categories[category_name].sort(key=lambda x: x["sku"])

        # Debug: Print categories and products
        app.logger.info(f"Loaded categories: {list(categories.keys())}")

        if request.method == 'POST':
            # Get the selected category from the form
            selected_category = request.form.get('category_select')

            if selected_category:
                for product in categories.get(selected_category, []):
                    # Get the new price from the form
                    new_price = request.form.get(f"new_price_{selected_category}_{product['id']}")

                    update_data = {}

                    # Update price if the new price is different from the old one
                    if new_price and new_price != str(product["price"]):
                        update_data["regular_price"] = str(new_price)

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
        return f"An error occurred: {e}", 500



# @app.route('/price_edit', methods=['GET', 'POST'])
# def price_edit():
#     try:
#         # Fetch products from WooCommerce API
#         response = wcapi.get("products", params={"per_page": 100})
#         if not response.ok:
#             app.logger.error(f"Failed to fetch products: {response.text}")
#             return f"Error fetching products: {response.text}"

#         # Prepare categories and products for display
#         products = response.json()
#         categories = {}
#         for product in products:
#             # Initialize fields
#             net_weight = "N/A"
#             packing = "N/A"

#             # Check for 'net_weight' in product attributes
#             attributes = product.get("attributes", [])
#             for attribute in attributes:
#                 if attribute.get("name") == "Net Weight":
#                     net_weight = attribute.get("options", ["N/A"])[0]  # Assuming the value is in the options list

#             # Also, check for packing in meta_data
#             meta_data = product.get("meta_data", [])
#             for meta in meta_data:
#                 if meta.get("key") == "packing":
#                     packing = meta.get("value", "N/A")

#             # Clean and format net_weight if it's not "N/A"
#             if net_weight != "N/A":
#                 net_weight = net_weight.strip().replace(" Kg", "")  # Clean if "Kg" exists

#             # Organize products by category
#             for category in product.get("categories", []):
#                 category_name = category["name"]
#                 if category_name not in categories:
#                     categories[category_name] = []
#                 categories[category_name].append({
#                     "sku": product.get("sku", "N/A"),
#                     "name": product.get("name", "N/A"),
#                     "price": "{:.2f}".format(float(product.get("price", 0))),
#                     "weight": product.get("weight", "N/A"),
#                     "net_weight": net_weight,
#                     "packing": packing,
#                     "id": product.get("id"),
#                 })

#         # Sort products by SKU within each category
#         for category_name in categories:
#             categories[category_name].sort(key=lambda x: x["sku"])

#         # Debug: Print categories and products
#         print(f"Loaded categories: {list(categories.keys())}")
#         for category_name, products in categories.items():
#             print(f"Category: {category_name}")
#             for product in products:
#                 print(f"  SKU: {product['sku']} | Name: {product['name']} | Price: {product['price']} | Weight: {product['weight']} | Net Weight: {product['net_weight']} | Packing: {product['packing']}")

#         if request.method == 'POST':
#             # Get the selected category from the form
#             selected_category = request.form.get('category_select')

#             if selected_category:
#                 for product in categories.get(selected_category, []):
#                     # Get the new values from the form
#                     new_price = request.form.get(f"new_price_{selected_category}_{product['id']}")
#                     new_weight = request.form.get(f"new_weight_{selected_category}_{product['id']}")
#                     new_net_weight = request.form.get(f"new_net_weight_{selected_category}_{product['id']}")
#                     new_packing = request.form.get(f"new_packing_{selected_category}_{product['id']}")  # Get new packing value

#                     # Debug print
#                     print(f"Debug: SKU: {product['sku']} Name: {product['name']} New Price: {new_price} New Weight: {new_weight} Current Net Weight: {product['net_weight']} New Net Weight: {new_net_weight} New Packing: {new_packing}")

#                     update_data = {}

#                     # Update price if the new price is different from the old one
#                     if new_price and new_price != str(product["price"]):
#                         update_data["regular_price"] = str(new_price)
                    
#                     # Update weight if the new weight is different from the old one
#                     if new_weight and new_weight != str(product["weight"]):
#                         update_data["weight"] = str(new_weight)
                    
#                     # Update net weight if the new net weight is provided
#                     if new_net_weight and new_net_weight != product["net_weight"]:
#                         update_data["attributes"] = [{
#                             "name": "Net Weight",
#                             "options": [new_net_weight],
#                             "visible": True 
#                         }]
                    
#                     # Update packing if the new packing value is provided
#                     #if new_packing and new_packing != product["packing"]:
#                     #    update_data.setdefault("meta_data", []).append({"key": "packing", "value": str(new_packing)})

#                     if update_data:
#                         try:
#                             # Send update to WooCommerce API
#                             response = wcapi.put(f"products/{product['id']}", update_data)
#                             if not response.ok:
#                                 app.logger.error(f"Failed to update product {product['id']}: {response.text}")
#                             else:
#                                 app.logger.info(f"Product {product['id']} updated with {update_data}.")
#                         except Exception as e:
#                             app.logger.error(f"Error updating product {product['id']}: {e}")

#             # After processing the form, redirect to the same page
#             return redirect('/price_edit')

#         # Render the price_edit page with categories and products
#         return render_template("price_edit.html", categories=categories, category_names=list(categories.keys()))

#     except Exception as e:
#         # Log and return error if an exception occurs
#         app.logger.error(f"An error occurred: {e}")
#         return page_reload(e)






#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/weight_edit', methods=['GET', 'POST'])
def weight_edit():
    try:
        # Fetch products from WooCommerce API with pagination
        products = []
        page = 1
        per_page = 100  # Set the maximum allowed per_page (100 is the max for WooCommerce)

        while True:
            # Fetch a page of products
            response = wcapi.get("products", params={"per_page": per_page, "page": page})
            if not response.ok:
                app.logger.error(f"Failed to fetch products: {response.text}")
                return f"Error fetching products: {response.text}", 500

            page_products = response.json()

            if not page_products:
                break  # No more products to fetch

            products.extend(page_products)  # Add fetched products to the list
            page += 1  # Move to the next page

        # Prepare categories and products for display
        categories = {}

        for product in products:
            # Log product name to terminal for debugging
            print(f"Processing product: {product.get('name', 'Unnamed Product')}")

            # Initialize fields
            net_weight = "N/A"
            packaging = "N/A"

            # Check for 'Net Weight' and 'Packaging' in product attributes
            attributes = product.get("attributes", [])
            for attribute in attributes:
                if attribute.get("name") == "Net Weight":
                    net_weight = attribute.get("options", ["N/A"])[0]
                elif attribute.get("name") == "Packaging":
                    packaging = attribute.get("options", ["N/A"])[0]

            # Organize products by category
            for category in product.get("categories", []):
                category_name = category["name"]
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append({
                    "sku": product.get("sku", "N/A"),
                    "name": product.get("name", "N/A"),
                    "weight": product.get("weight", "N/A"),
                    "net_weight": net_weight,
                    "packaging": packaging,
                    "id": product.get("id"),
                })

        for category in categories:
            categories[category] = sorted(categories[category], key=lambda x: x['sku'])

        # Handle POST request for updating weight and net weight
        if request.method == 'POST':
            selected_category = request.form.get('category_select')

            if selected_category:
                for product in categories.get(selected_category, []):
                    new_weight = request.form.get(f"new_weight_{selected_category}_{product['id']}")
                    new_net_weight = request.form.get(f"new_net_weight_{selected_category}_{product['id']}")

                    update_data = {
                        # Always include the current packaging value to keep it unchanged
                        "attributes": [
                            {
                                "name": "Packaging",
                                "options": [product["packaging"]],
                                "visible": True
                            }
                        ]
                    }

                    # Update weight if it's different
                    if new_weight and new_weight != str(product["weight"]):
                        update_data["weight"] = str(new_weight)

                    # Update net weight if it's different
                    if new_net_weight and new_net_weight != product["net_weight"]:
                        update_data["attributes"].append({
                                "name": "Net Weight",
                                "options": [new_net_weight],
                                "visible": True
                            })

                    # Only send update if there's data to change
                    if update_data:
                        try:
                            response = wcapi.put(f"products/{product['id']}", update_data)
                            if not response.ok:
                                app.logger.error(f"Failed to update product {product['id']}: {response.text}")
                            else:
                                app.logger.info(f"Successfully updated product {product['id']} with {update_data}.")
                        except Exception as e:
                            app.logger.error(f"Error updating product {product['id']}: {e}")

            return redirect('/weight_edit')

        # Render the weight_edit page with categories and products
        return render_template("weight_edit.html", categories=categories, category_names=list(categories.keys()))

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return f"An unexpected error occurred: {e}", 500


#----------------------------------------------------------------------------------------------------------------------------------
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    try:
        # Fetch orders from WooCommerce API
        response = wcapi.get("orders", params={"per_page": 100})
        if not response.ok:
            app.logger.error(f"Failed to fetch orders: {response.text}")
            return f"Error fetching orders: {response.text}"

        orders = response.json()
        order_statuses = {}

        # Group orders by status
        for order in orders:
            status = order.get("status", "unknown").capitalize()
            if status not in order_statuses:
                order_statuses[status] = []
            order_statuses[status].append({
                "id": order.get("id"),
                "number": order.get("number"),
                "date_created": order.get("date_created"),
                "total": order.get("total"),
                "customer_name": f"{order.get('billing', {}).get('first_name', '')} {order.get('billing', {}).get('last_name', '')}".strip(),
            })

        # Handle POST for updating order status
        if request.method == 'POST':
            order_id = request.form.get('order_id')
            new_status = request.form.get('new_status')

            if order_id and new_status:
                update_data = {"status": new_status.lower()}
                response = wcapi.put(f"orders/{order_id}", update_data)
                if response.ok:
                    app.logger.info(f"Order {order_id} updated to status '{new_status}'.")
                else:
                    app.logger.error(f"Failed to update order {order_id}: {response.text}")

            return redirect('/orders')

        return render_template('orders.html', order_statuses=order_statuses)

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return f"Error: {e}"



@app.route('/order_items/<int:order_id>', methods=['GET'])
def order_items(order_id):
    try:
        # Call WooCommerce API to get the order details
        response = wcapi.get(f"orders/{order_id}")
        
        # If the response is not OK, return an error message
        if not response.ok:
            app.logger.error(f"Failed to fetch order {order_id} details: {response.text}")
            return jsonify({"error": "Failed to fetch order details"}), 500

        # Parse the order data to extract items
        order_data = response.json()
        
        # Extract order line items
        items = [
            {
                "name": item.get("name"),
                "quantity": item.get("quantity"),
                "price": float(item.get("price", 0)),
                "total": float(item.get("total", 0))
            }
            for item in order_data.get("line_items", [])
        ]
        
        # Extract delivery charges (shipping) and discounts
        shipping_total = float(order_data.get("shipping_total", 0))
        discount_total = float(order_data.get("discount_total", 0))
        
        # Calculate the total net (items total without discount) and final total
        net_total = sum(item["total"] for item in items) + shipping_total
        final_total = net_total - discount_total
        
        # Return the details along with items, shipping, discount, net total, and final total
        return jsonify({
            "items": items,
            "shipping_total": shipping_total,
            "discount_total": discount_total,
            "net_total": net_total,
            "final_total": final_total
        }), 200

    except Exception as e:
        app.logger.error(f"Error fetching order items: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/change_order_status/<int:order_id>', methods=['POST'])
def change_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')

    # Check if the new status is provided
    if new_status:
        # Update order status using the WooCommerce API
        update_data = {"status": new_status.lower()}  # WooCommerce expects lowercase status values

        try:
            # Send a PUT request to update the order status
            response = wcapi.put(f"orders/{order_id}", update_data)

            # Check if the response is successful
            if response.ok:
                return jsonify({'success': True, 'message': f"Order {order_id} updated to {new_status}"})
            else:
                app.logger.error(f"Failed to update order {order_id}: {response.text}")
                return jsonify({'success': False, 'error': f"Failed to update order: {response.text}"})

        except Exception as e:
            app.logger.error(f"Error updating order {order_id}: {e}")
            return jsonify({'success': False, 'error': str(e)})

    else:
        return jsonify({'success': False, 'error': 'No status provided'})

#----------------------------------------------------------------------------------------------------------------------------------

# Function to run Flask server in a separate thread
def run_server():
    app.run(debug=True, port=8080, use_reloader=False)



# Function to open the web page in the default browser
def stock_edit():
    webbrowser.open("http://127.0.0.1:8080/stock_edit")

def price_edit():
    webbrowser.open("http://127.0.0.1:8080/price_edit")

def weight_edit():
    webbrowser.open("http://127.0.0.1:8080/weight_edit")    

def order_edit():
    webbrowser.open("http://127.0.0.1:8080/orders")    