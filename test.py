from woocommerce import API

# WooCommerce API credentials
wcapi = API(
    url="https://agrospicefoodpackers.com",  # Replace with your WooCommerce store URL
    consumer_key="ck_f16cf35e84177a97ffaa460997463e939555d307",  # Replace with your consumer key
    consumer_secret="cs_56d85bc97fda6ba982f56bcfe454aa7f372a0a5b",  # Replace with your consumer secret
    version="wc/v3"
)

def fetch_all_products():
    try:
        # Initialize product list
        all_products = []
        page = 1

        while True:
            # Fetch products page by page
            response = wcapi.get("products", params={"per_page": 100, "page": page})
            if not response.ok:
                print(f"Failed to fetch products: {response.text}")
                break

            products = response.json()
            if not products:
                break  # Exit loop if no more products

            all_products.extend(products)
            page += 1

        # Print product details
        for product in all_products:
            print(f"ID: {product.get('id')}, Name: {product.get('name')}, SKU: {product.get('sku')}, Price: {product.get('price')}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Fetch and print all products
fetch_all_products()
