"""
Hlavní spouštěcí soubor pro Baselinker Product Management aplikaci
"""

from baselinker_cli import BaselinkerClient


def main():
    """Hlavní funkce aplikace"""
    token = "6006390-6000727-7Y05TI6LMN7VFEYOEWGSVINHOE8ZUPBHV9YA6N6STVVSGM02F248NZX4D1KZXLNR"
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

        # Get detailed product data for extra fields
        print("Fetching detailed product data for extra fields...")
        product_ids = [product.get('id') for product in products if product.get('id')]
        detailed_products = {}
        
        if product_ids:
            try:
                # Get detailed data for all products at once
                detailed_data = client.get_products_detailed(product_ids, inventory_id)
                detailed_products = detailed_data
                print(f"Retrieved detailed data for {len(detailed_products)} products")
            except Exception as e:
                print(f"Warning: Could not fetch detailed product data: {str(e)}")
                print("Showing basic product data only...")

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
                    # Get all extra_field_* keys from text_fields
                    extra_fields = {k: v for k, v in text_fields.items() if k.startswith('extra_field_')}
                    if len(extra_fields) >= 1:
                        field1 = list(extra_fields.values())[0]
                    if len(extra_fields) >= 2:
                        field2 = list(extra_fields.values())[1]
            
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
                    if text_fields:
                        extra_fields = {k: v for k, v in text_fields.items() if k.startswith('extra_field_')}
                        if len(extra_fields) >= 2:
                            current_field2 = list(extra_fields.values())[1]
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
        print(f"Error connecting to Baselinker API: {str(e)}")
        print("Please check your internet connection and API token.")


if __name__ == "__main__":
    main()
