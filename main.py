"""
Main entry point for Baselinker Product Management application
"""

import os
import sys
import logging
from pathlib import Path
from baselinker_cli import BaselinkerClient

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger = logging.getLogger(__name__)
        logger.info(f"Loaded environment variables from {env_path}")
except ImportError:
    # python-dotenv not installed, will use system environment variables
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main application function"""
    # Get token from environment variable
    token = os.getenv('BASELINKER_API_TOKEN')
    
    if not token:
        logger.error("BASELINKER_API_TOKEN environment variable is not set!")
        sys.exit(1)
    
    client = BaselinkerClient(token)

    print("=== Baselinker Product Management ===")
    print("Fetching available inventories...")
    
    try:
        inventories = client.get_inventories()
        if not inventories:
            print("No inventories found in your Baselinker account.")
            return
        
        print("Available inventories:")
        for inventory in inventories:
            print(f"  - Inventory ID: {inventory['inventory_id']}, Name: {inventory.get('name', 'N/A')}")
        
        # Use the first available inventory
        inventory_id = inventories[0]['inventory_id']
        print(f"\nUsing inventory: {inventory_id}")

        print("\nFetching products...")
        products = client.get_products(inventory_id)
        print(f"Found {len(products)} products in inventory {inventory_id}")

        if not products:
            print("No products found in the inventory.")
            return

        # Get available extra fields for this inventory
        try:
            extra_fields = client.get_inventory_extra_fields(inventory_id)
            field1_id = extra_fields[0]['extra_field_id'] if len(extra_fields) >= 1 else None
            field2_id = extra_fields[1]['extra_field_id'] if len(extra_fields) >= 2 else None
            logger.info(f"Extra fields: Field1 ID={field1_id}, Field2 ID={field2_id}")
        except Exception as e:
            logger.warning(f"Could not fetch extra fields: {str(e)}")
            field1_id = None
            field2_id = None

        # Get detailed product data for extra fields
        print("Fetching detailed product data for extra fields...")
        product_ids = [product.get('id') for product in products if product.get('id')]
        detailed_products = {}
        
        if product_ids:
            try:
                # Get detailed data for all products at once
                detailed_data = client.get_products_detailed(product_ids, inventory_id)
                detailed_products = detailed_data
                logger.info(f"Retrieved detailed data for {len(detailed_products)} products")
            except Exception as e:
                logger.warning(f"Could not fetch detailed product data: {str(e)}")
                logger.info("Showing basic product data only...")

        # Display all products with required fields
        print("\n=== All Products ===")
        print(f"{'ID':<12} {'SKU':<15} {'EAN':<15} {'Name':<20} {'Price':<10} {'Field1':<15} {'Field2':<15}")
        print("-" * 120)
        
        for product in products:
            product_id = product.get('id', 'N/A')
            sku = product.get('sku', 'N/A')
            ean = product.get('ean', 'N/A')
            name = product.get('name', 'N/A')
            
            # Get price - try to get the main price or first available price
            prices = product.get('prices', {})
            price = 'N/A'
            if prices:
                # Get the first available price or use a default price field
                price = list(prices.values())[0] if prices else 'N/A'
            
            # Try to get extra fields from detailed data
            field1 = 'N/A'
            field2 = 'N/A'

            # Convert product_id to string since detailed_products uses string keys

            product_id_str = str(product_id)

            if product_id_str in detailed_products:
                detail_product = detailed_products[product_id_str]
                text_fields = detail_product.get('text_fields', {})
                if text_fields:
                    # Get specific extra fields by dynamically retrieved IDs
                    if field1_id:
                        field1 = text_fields.get(f'extra_field_{field1_id}', 'N/A')
                    if field2_id:
                        field2 = text_fields.get(f'extra_field_{field2_id}', 'N/A')
            
            print(f"{product_id:<12} {sku:<15} {ean:<15} {name[:19]:<20} {price:<10} {field1:<15} {field2:<15}")

        # User interaction for updating field2
        print("\n=== Update Product Field2 ===")
        while True:
            try:
                product_id_input = input("\nEnter product ID to update (or 'quit' to exit): ").strip()
                
                if product_id_input.lower() == 'quit':
                    print("Exiting...")
                    break
                
                product_id = int(product_id_input)
                
                # Find the product
                selected_product = None
                for product in products:
                    if product.get('id') == product_id:
                        selected_product = product
                        break
                
                if not selected_product:
                    print(f"Product with ID {product_id} not found.")
                    continue
                
                print(f"\nSelected product:")
                print(f"  ID: {selected_product.get('id')}")
                print(f"  SKU: {selected_product.get('sku')}")
                print(f"  Name: {selected_product.get('name')}")
                # Try to get current field2 value from detailed data
                current_field2 = 'N/A'
                product_id_str = str(product_id)

                if product_id_str in detailed_products:
                    detail_product = detailed_products[product_id_str]
                    text_fields = detail_product.get('text_fields', {})
                    if text_fields and field2_id:
                        # Get specific Field2 by dynamically retrieved ID
                        current_field2 = text_fields.get(f'extra_field_{field2_id}', 'N/A')
                print(f"  Current Field2: {current_field2}")
                
                new_value = input("Enter new value for Field2: ").strip()
                
                if not new_value:
                    print("Value cannot be empty.")
                    continue
                
                print(f"\nUpdating product {product_id} with new Field2 value: '{new_value}'")
                
                # Update the product
                success = client.update_product_field2(product_id, inventory_id, new_value)
                
                if success:
                    print("Product updated successfully!")
                    
                    # Update the local product data
                    selected_product['extra_field_2'] = new_value
                    
                    # Show updated product info
                    print(f"\nUpdated product:")
                    print(f"  ID: {selected_product.get('id')}")
                    print(f"  SKU: {selected_product.get('sku')}")
                    print(f"  Name: {selected_product.get('name')}")
                    print(f"  New Field2: {selected_product.get('extra_field_2')}")
                else:
                    print("Failed to update product. Please try again.")
                
            except ValueError:
                print("Please enter a valid product ID (number) or 'quit'.")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"An error occurred: {str(e)}")

    except Exception as e:
        logger.error(f"Error connecting to Baselinker API: {str(e)}")
        logger.error("Please check your internet connection and API token.")
        sys.exit(1)


if __name__ == "__main__":
    main()
