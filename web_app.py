"""
Streamlit Web Application for Baselinker Product Management
Simple web interface for non-technical users to manage product extra fields
"""

import os
import streamlit as st
import pandas as pd
from pathlib import Path
from baselinker_cli import BaselinkerClient

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def get_client():
    """Get BaselinkerClient instance with token from environment"""
    token = os.getenv('BASELINKER_API_TOKEN')
    if not token:
        st.error("BASELINKER_API_TOKEN not set in .env file!")
        st.stop()
    return BaselinkerClient(token)


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Baselinker Product Manager",
        layout="wide"
    )
    
    st.title("Baselinker Product Management")
    st.markdown("Manage product extra fields easily")
    
    # Initialize client
    client = get_client()
    
    # Get inventories
    try:
        with st.spinner("Loading inventories..."):
            inventories = client.get_inventories()
        
        if not inventories:
            st.error("No inventories found!")
            return
        
        # Inventory selector
        inventory_options = {
            inv['inventory_id']: f"{inv.get('name', 'N/A')} (ID: {inv['inventory_id']})"
            for inv in inventories
        }
        
        selected_inventory_id = st.selectbox(
            "Select Inventory:",
            options=list(inventory_options.keys()),
            format_func=lambda x: inventory_options[x]
        )
        
        # Get extra fields for this inventory
        extra_fields = client.get_inventory_extra_fields(selected_inventory_id)
        if len(extra_fields) < 2:
            st.error("Inventory needs at least 2 extra fields!")
            return
        
        field1_id = extra_fields[0]['extra_field_id']
        field1_name = extra_fields[0]['name']
        field2_id = extra_fields[1]['extra_field_id']
        field2_name = extra_fields[1]['name']
        
        st.info(f"Field1: {field1_name} | Field2: {field2_name}")
        
        # Get products
        with st.spinner("Loading products..."):
            products = client.get_products(selected_inventory_id)
            
            if not products:
                st.warning("No products found in this inventory.")
                return
            
            # Get detailed data
            product_ids = [p.get('id') for p in products if p.get('id')]
            detailed_products = client.get_products_detailed(product_ids, selected_inventory_id)
        
        # Prepare data for display
        product_data = []
        for product in products:
            product_id = product.get('id')
            product_id_str = str(product_id)
            
            # Get price
            prices = product.get('prices', {})
            price = list(prices.values())[0] if prices else 'N/A'
            
            # Get extra fields
            field1 = 'N/A'
            field2 = 'N/A'
            
            if product_id_str in detailed_products:
                text_fields = detailed_products[product_id_str].get('text_fields', {})
                field1 = text_fields.get(f'extra_field_{field1_id}', 'N/A')
                field2 = text_fields.get(f'extra_field_{field2_id}', 'N/A')
            
            product_data.append({
                'ID': product_id,
                'SKU': product.get('sku', 'N/A'),
                'EAN': product.get('ean', 'N/A'),
                'Name': product.get('name', 'N/A'),
                'Price': price,
                field1_name: field1,
                field2_name: field2
            })
        
        # Create DataFrame
        df = pd.DataFrame(product_data)
        
        st.markdown("---")
        st.subheader("Products")
        st.caption(f"Total: {len(df)} products")
        
        # Display editable table
        st.markdown("**Click on a cell in the '{}' column to edit**".format(field2_name))
        
        # Use st.data_editor for editable table
        edited_df = st.data_editor(
            df,
            disabled=['ID', 'SKU', 'EAN', 'Name', 'Price', field1_name],
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            key="product_table"
        )
        
        # Detect changes
        if not df.equals(edited_df):
            st.markdown("---")
            st.subheader("Changes Detected")
            
            # Find changed rows
            changes = []
            for idx in range(len(df)):
                if df.iloc[idx][field2_name] != edited_df.iloc[idx][field2_name]:
                    changes.append({
                        'product_id': int(edited_df.iloc[idx]['ID']),
                        'old_value': df.iloc[idx][field2_name],
                        'new_value': edited_df.iloc[idx][field2_name],
                        'name': edited_df.iloc[idx]['Name']
                    })
            
            if changes:
                st.write(f"**{len(changes)} product(s) will be updated:**")
                for change in changes:
                    st.write(f"- **{change['name']}** (ID: {change['product_id']}): `{change['old_value']}` → `{change['new_value']}`")
                
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("Save Changes", type="primary", use_container_width=True):
                        progress_bar = st.progress(0)
                        success_count = 0
                        
                        for i, change in enumerate(changes):
                            with st.spinner(f"Updating {change['name']}..."):
                                success = client.update_product_field2(
                                    change['product_id'],
                                    selected_inventory_id,
                                    change['new_value']
                                )
                                if success:
                                    success_count += 1
                                progress_bar.progress((i + 1) / len(changes))
                        
                        if success_count == len(changes):
                            st.success(f"All {success_count} products updated successfully!")
                            st.rerun()
                        else:
                            st.warning(f"Updated {success_count}/{len(changes)} products")
                
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)


if __name__ == "__main__":
    main()

