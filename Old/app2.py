import os
import json
from flask import Flask, render_template, request, redirect, url_for
from woocommerce import API
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import webbrowser
import sys

# Flask app
app = Flask(__name__)

# Path to the data file
data_file = "data.json"

# Function to load API credentials
def load_credentials():
    if os.path.exists(data_file):
        try:
            with open(data_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid data.json file format.")
    return {}

# Function to save API credentials
def save_credentials(credentials):
    with open(data_file, "w") as f:
        json.dump(credentials, f, indent=4)

def prompt_for_credentials():
    # Create a temporary hidden root window
    temp_root = tk.Tk()
    temp_root.withdraw()  # Hide the root window

    input_window = tk.Toplevel(temp_root)  # Create a new window as a child of temp_root
    input_window.title("Enter API Credentials")
    input_window.geometry("400x250")

    tk.Label(input_window, text="WooCommerce Store URL:", font=("Arial", 10)).pack(pady=5)
    url_entry = tk.Entry(input_window, width=50)
    url_entry.pack(pady=5)

    tk.Label(input_window, text="Consumer Key:", font=("Arial", 10)).pack(pady=5)
    key_entry = tk.Entry(input_window, width=50)
    key_entry.pack(pady=5)

    tk.Label(input_window, text="Consumer Secret:", font=("Arial", 10)).pack(pady=5)
    secret_entry = tk.Entry(input_window, width=50, show="*")
    secret_entry.pack(pady=5)

    def save_and_close():
        url = url_entry.get().strip()
        consumer_key = key_entry.get().strip()
        consumer_secret = secret_entry.get().strip()

        if not url or not consumer_key or not consumer_secret:
            messagebox.showwarning("Incomplete Information", "All fields must be filled!")
            return

        credentials["url"] = url
        credentials["consumer_key"] = consumer_key
        credentials["consumer_secret"] = consumer_secret
        save_credentials(credentials)
        temp_root.destroy()  # Destroy the temporary root

    def close_without_saving():
        temp_root.destroy()
        sys.exit("Credentials were not provided. Exiting program.")  # Exit with a clear message

    input_window.protocol("WM_DELETE_WINDOW", close_without_saving)  # Handle window close event
    tk.Button(input_window, text="Save", command=save_and_close, font=("Arial", 10)).pack(pady=10)
    input_window.mainloop()


# Load or prompt for credentials
credentials = load_credentials()
if not credentials.get("url") or not credentials.get("consumer_key") or not credentials.get("consumer_secret"):
    prompt_for_credentials()

# WooCommerce API setup
wcapi = API(
    url=credentials["url"],
    consumer_key=credentials["consumer_key"],
    consumer_secret=credentials["consumer_secret"],
    version="wc/v3"
)

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

# Function to stop the server
def stop_server():
    messagebox.showinfo("Server Stopped", "Stopping the server and closing the app.")
    root.destroy()
    exit()

# Function to open the web page in the default browser
def open_home_page():
    webbrowser.open("http://127.0.0.1:8080")

# Function to edit credentials
def edit_credentials():
    prompt_for_credentials()
    messagebox.showinfo("Success", "API credentials updated successfully.")

# GUI for controlling the server
def create_gui():
    global root
    root = tk.Tk()
    root.title("Flask Server")
    root.geometry("300x250")

    label = tk.Label(root, text="Flask Server is running...", font=("Arial", 12))
    label.pack(pady=20)

    open_button = tk.Button(root, text="Edit Product Stock", command=open_home_page, font=("Arial", 10))
    open_button.pack(pady=10)

    edit_button = tk.Button(root, text="Edit API Credentials", command=edit_credentials, font=("Arial", 10))
    edit_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop Server", command=stop_server, font=("Arial", 10), bg="red", fg="white")
    stop_button.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    create_gui()
