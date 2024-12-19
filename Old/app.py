from flask import Flask, render_template, request, redirect, url_for
from woocommerce import API
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser  # Import the webbrowser module
import sys

# Flask app
app = Flask(__name__)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# WooCommerce API credentials
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
wcapi = API(
    url="https://agrospicefoodpackers.com",  # Replace with your WooCommerce store URL
    consumer_key="ck_f16cf35e84177a97ffaa460997463e939555d307",  # Replace with your WooCommerce Consumer Key
    consumer_secret="cs_56d85bc97fda6ba982f56bcfe454aa7f372a0a5b",  # Replace with your WooCommerce Consumer Secret
    version="wc/v3"
)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Flask home page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
@app.route('/', methods=['GET', 'POST'])
def display_products():
    try:
        # Fetch products from WooCommerce
        response = wcapi.get("products", params={"per_page": 100})
        if not response.ok:
            app.logger.error(f"Failed to fetch products: {response.text}")
            return f"Error fetching products: {response.text}"

        products = response.json()

        # Group products by category
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

        # Sort products by SKU within each category
        for category_name in categories:
            categories[category_name].sort(key=lambda x: x["sku"])

        if request.method == 'POST':
            selected_category = request.form.get('category_select')

            if selected_category:
                # Loop through the products in the selected category and update stock
                for product in categories.get(selected_category, []):
                    new_stock = request.form.get(f"new_stock_{selected_category}_{product['id']}")
                    print("************** Updating:", product['sku'], product['name'], " = ",new_stock)
                    if new_stock and new_stock != str(product['stock']):
                        # Update the product stock in WooCommerce
                        try:
                            data = {"stock_quantity": int(new_stock)}
                            response = wcapi.put(f"products/{product['id']}", data)
                            if not response.ok:
                                app.logger.error(f"Failed to update product {product['id']}: {response.text}")
                            else:
                                app.logger.info(f"Product {product['id']} updated to {new_stock} stock.")
                        except Exception as e:
                            app.logger.error(f"Error updating product {product['id']}: {e}")

            # Refresh the products after update
            return redirect('/')

        return render_template("products.html", categories=categories, category_names=list(categories.keys()))

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return f"An error occurred: {e}"




#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Function to run Flask server in a separate thread
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def run_server():
    app.run(debug=True, port=8080, use_reloader=False)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Function to stop the server
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def stop_server():
    messagebox.showinfo("Server Stopped", "Stopping the server and closing the app.")
    root.destroy()  # Closes the Tkinter window
    exit()  # Exits the application

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Function to open the web page in the default browser
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def open_home_page():
    webbrowser.open("http://127.0.0.1:8080")  # Opens the Flask home page in the default browser

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# GUI for controlling the server
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def create_gui():
    global root
    root = tk.Tk()
    root.title("Flask Server")
    root.geometry("300x200")

    # Set custom icon for the window (path to your .ico file)
    if getattr(sys, 'frozen', False):  # Check if running as a bundled .exe
        icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")  # _MEIPASS is where PyInstaller extracts files
    else:
        icon_path = "app_icon.ico"  # If running in development mode

    try:
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Error setting icon: {e}")

    # Add a label
    label = tk.Label(root, text="Flask Server is running...", font=("Arial", 12))
    label.pack(pady=20)

    # Add a button to open the web home page
    open_button = tk.Button(root, text="Open Home Page", command=open_home_page, font=("Arial", 10))
    open_button.pack(pady=10)

    # Add a stop button
    stop_button = tk.Button(root, text="Stop Server", command=stop_server, font=("Arial", 10), bg="red", fg="white")
    stop_button.pack(pady=10)

    root.mainloop()






if __name__ == '__main__':
    # Run Flask server in a separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Launch the GUI
    create_gui()
