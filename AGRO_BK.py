import os
import json
from flask import Flask, render_template, request, redirect, url_for
from woocommerce import API
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse
#import webbrowser
import sys
import time

from flask_app import *

# Path to the data file
data_file = "data.json"
# WooCommerce API setup

# Function to load API credentials-----------------------------------------------------------------------------------------
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

# Function to validate credentials
def validate_credentials(url, consumer_key, consumer_secret, progress_bar):
    # Simulate progress
    progress_bar["value"] = 20
    progress_bar.update()
    time.sleep(0.5)

    # Basic validation for URL format
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        progress_bar["value"] = 0
        progress_bar.update()
        return False, "Invalid URL format."

    progress_bar["value"] = 50
    progress_bar.update()
    time.sleep(0.5)

    # Check non-empty Consumer Key and Consumer Secret
    if not consumer_key or not consumer_secret:
        progress_bar["value"] = 0
        progress_bar.update()
        return False, "Consumer Key and Secret cannot be empty."

    progress_bar["value"] = 80
    progress_bar.update()
    time.sleep(0.5)

    # Attempt to connect to the WooCommerce API
    try:
        test_wcapi = API(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3"
        )
        response = test_wcapi.get("system_status")
        if not response.ok:
            progress_bar["value"] = 0
            progress_bar.update()
            return False, f"API connection failed: {response.status_code} {response.text}"
    except Exception as e:
        progress_bar["value"] = 0
        progress_bar.update()
        return False, f"An error occurred during validation: {e}"

    progress_bar["value"] = 100
    progress_bar.update()
    time.sleep(0.5)
    return True, "Valid credentials."

def prompt_for_credentials():
    # Create a temporary hidden root window
    temp_root = tk.Tk()
    temp_root.withdraw()  # Hide the root window

    input_window = tk.Toplevel(temp_root)  # Create a new window as a child of temp_root
    input_window.title("Enter API Credentials")
    input_window.geometry("400x350")

    tk.Label(input_window, text="WooCommerce Store URL:", font=("Arial", 10)).pack(pady=5)
    url_entry = tk.Entry(input_window, width=50)
    url_entry.pack(pady=5)

    tk.Label(input_window, text="Consumer Key:", font=("Arial", 10)).pack(pady=5)
    key_entry = tk.Entry(input_window, width=50)
    key_entry.pack(pady=5)

    tk.Label(input_window, text="Consumer Secret:", font=("Arial", 10)).pack(pady=5)
    secret_entry = tk.Entry(input_window, width=50, show="*")
    secret_entry.pack(pady=5)

    # Add a progress bar
    progress_bar = ttk.Progressbar(input_window, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)

    def save_and_close():
        url = url_entry.get().strip()
        consumer_key = key_entry.get().strip()
        consumer_secret = secret_entry.get().strip()

        is_valid, message = validate_credentials(url, consumer_key, consumer_secret, progress_bar)
        if not is_valid:
            messagebox.showerror("Validation Error", message)
            progress_bar["value"] = 0
            return

        credentials["url"] = url
        credentials["consumer_key"] = consumer_key
        credentials["consumer_secret"] = consumer_secret
        save_credentials(credentials)
        messagebox.showinfo("Success", "API credentials validated and saved successfully.")
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

wcapi = API(
    url=credentials["url"],
    consumer_key=credentials["consumer_key"],
    consumer_secret=credentials["consumer_secret"],
    version="wc/v3"
)

# GUI for controlling the server
# def create_gui():
#     global root
#     root = tk.Tk()
#     root.title("Flask Server")
#     root.geometry("300x250")

#     # Set custom icon for the window (path to your .ico file)
#     if getattr(sys, 'frozen', False):  # Check if running as a bundled .exe
#         icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")  # _MEIPASS is where PyInstaller extracts files
#     else:
#         icon_path = "app_icon.ico"  # If running in development mode

#     try:
#         root.iconbitmap(icon_path)
#     except Exception as e:
#         print(f"Error setting icon: {e}")

#     label = tk.Label(root, text="Flask Server is running...", font=("Arial", 12))
#     label.pack(pady=20)

#     open_button = tk.Button(root, text="Edit Product Stock", command=open_home_page, font=("Arial", 10))
#     open_button.pack(pady=10)

#     edit_button = tk.Button(root, text="Edit API Credentials", command=edit_credentials, font=("Arial", 10))
#     edit_button.pack(pady=10)

#     stop_button = tk.Button(root, text="Stop Server", command=stop_server, font=("Arial", 10), bg="red", fg="white")
#     stop_button.pack(pady=10)

#     root.mainloop()
def create_gui():
    global root
    root = tk.Tk()
    root.title("Flask Server")
    root.geometry("300x250")
    
    # Set custom icon for the window (handles both development and PyInstaller builds)
    try:
        if getattr(sys, 'frozen', False):  # Running as a PyInstaller .exe
            icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")  # Extracted temporary folder
        else:
            icon_path = "app_icon.ico"  # Running in development mode
        
        root.iconbitmap(icon_path)  # Set the icon for the taskbar and status bar
    except Exception as e:
        print(f"Error setting icon: {e}")


    label = tk.Label(root, text="Flask Server is running...", font=("Arial", 12))
    label.pack(pady=20)

    open_button = tk.Button(root, text="Edit Product Stock", command=stock_edit, font=("Arial", 10))
    open_button.pack(pady=10)

    open_button = tk.Button(root, text="Edit Product Price", command=price_edit, font=("Arial", 10))
    open_button.pack(pady=10)

    edit_button = tk.Button(root, text="Edit API Credentials", command=edit_credentials, font=("Arial", 10))
    edit_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop Server", command=stop_server, font=("Arial", 10), bg="red", fg="white")
    stop_button.pack(pady=10)

    root.mainloop()


# Function to stop the server
def stop_server():
    messagebox.showinfo("Server Stopped", "Stopping the server and closing the app.")
    root.destroy()
    exit()


# Function to edit credentials
def edit_credentials():
    prompt_for_credentials()
    messagebox.showinfo("Success", "API credentials updated successfully.")



if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    create_gui()
