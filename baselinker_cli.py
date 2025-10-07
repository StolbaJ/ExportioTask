"""
Baselinker API Client
Module for communication with Baselinker API for product retrieval and updates
"""

import requests
import json
import logging
from typing import List, Dict

# Configure logging
logger = logging.getLogger(__name__)

class BaselinkerClient:
    """Client for communication with Baselinker API"""

    def __init__(self, token: str):
        """
        Initialize client with API token

        Args:
            token (str): API token for Baselinker
        """
        self.token = token
        self.base_url = "https://api.baselinker.com/connector.php"
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-BLToken': token
        }

    def _make_request(self, method: str, parameters: Dict = None) -> Dict:
        """
        Creates HTTP request to Baselinker API

        Args:
            method (str): API method name
            parameters (Dict): Parameters for API call

        Returns:
            Dict: API response

        Raises:
            Exception: If an error occurs during API communication
        """
        if parameters is None:
            parameters = {}

        data = {
            'method': method,
            'parameters': json.dumps(parameters)
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, data=data)
            response.raise_for_status()

            result = response.json()

            if result.get('status') == 'ERROR':
                raise Exception(f"API Error: {result.get('error_message', 'Unknown error')}")

            return result

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {str(e)}")

    def get_inventories(self) -> List[Dict]:
        """Get list of all inventories"""
        result = self._make_request('getInventories')
        return result.get('inventories', [])

    def get_products(self, inventory_id: int) -> List[Dict]:
        """
        Get list of all products from given inventory

        Args:
            inventory_id (int): Inventory ID

        Returns:
            List[Dict]: List of products with their data
        """
        parameters = {
            'inventory_id': inventory_id
        }

        result = self._make_request('getInventoryProductsList', parameters)

        if 'products' in result:
            # Baselinker API returns products as dict with ID as keys
            # We need to convert it to list
            products_dict = result['products']
            if isinstance(products_dict, dict):
                return list(products_dict.values())
            else:
                return products_dict
        else:
            return []

    def update_product_field2(self, product_id: int, inventory_id: int, new_value: str) -> bool:
        """
        Update the second supplementary field of a product

        Args:
            product_id (int): Product ID to update
            inventory_id (int): Inventory ID
            new_value (str): New value for the second supplementary field

        Returns:
            bool: True if update was successful
        """
        # First, get available extra fields
        try:
            extra_fields = self.get_inventory_extra_fields(inventory_id)
            logger.debug(f"Available extra fields: {extra_fields}")
            
            # Find the second extra field (index 1)
            if len(extra_fields) < 2:
                logger.error("Inventory doesn't have enough extra fields (need at least 2).")
                return False
            
            field_id = extra_fields[1]['extra_field_id']  # Second field (index 1)
            field_name = extra_fields[1]['name']
            logger.info(f"Using extra field: {field_name} (ID: {field_id})")
            
        except Exception as e:
            logger.error(f"Error getting extra fields: {str(e)}")
            return False

        # Get current product data
        try:
            current_product = self.get_product_details(product_id, inventory_id)
            if not current_product:
                logger.warning(f"Product with ID {product_id} not found in detailed data.")
                logger.info("Trying to get basic product data...")
                
                # Try to get basic data from getInventoryProductsList
                all_products = self.get_products(inventory_id)
                current_product = None
                for product in all_products:
                    if product.get('id') == product_id:
                        current_product = product
                        break
                
                if not current_product:
                    logger.error(f"Product with ID {product_id} not found in basic data either.")
                    return False
                
                logger.debug(f"Using basic product data: {current_product}")
            else:
                logger.debug(f"Current product data: {current_product}")
        except Exception as e:
            logger.error(f"Error getting product data: {str(e)}")
            return False

        # Get product name from text_fields or main structure
        product_name = current_product.get('name', '')
        text_fields = current_product.get('text_fields', {})
        if text_fields and 'name' in text_fields:
            product_name = text_fields['name']
        
        # Prepare parameters for update
        parameters = {
            'inventory_id': str(inventory_id),
            'product_id': str(product_id),
            'sku': current_product.get('sku', ''),
            'ean': current_product.get('ean', ''),
            'text_fields': {
                'name': product_name,
                f'extra_field_{field_id}': new_value
            }
        }
        
        logger.debug(f"Updating with parameters: {parameters}")

        try:
            result = self._make_request('addInventoryProduct', parameters)
            return result.get('status') == 'SUCCESS'
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            return False

    def get_inventory_extra_fields(self, inventory_id: int) -> List[Dict]:
        """
        Get list of available extra fields for inventory

        Args:
            inventory_id (int): Inventory ID

        Returns:
            List[Dict]: List of extra fields
        """
        parameters = {
            'inventory_id': inventory_id
        }

        result = self._make_request('getInventoryExtraFields', parameters)
        return result.get('extra_fields', [])

    def get_products_detailed(self, product_ids: List[int], inventory_id: int) -> Dict:
        """
        Get detailed information for multiple products at once

        Args:
            product_ids (List[int]): List of product IDs
            inventory_id (int): Inventory ID

        Returns:
            Dict: Dictionary with ID as keys and detailed data as values
        """
        parameters = {
            'inventory_id': inventory_id,
            'products': product_ids
        }

        result = self._make_request('getInventoryProductsData', parameters)
        logger.debug(f"getInventoryProductsData response: {result}")
        
        if 'products' in result and result['products']:
            products = result['products']
            if isinstance(products, dict):
                logger.debug(f"Products returned as dict with {len(products)} items")
                return products
            else:
                # If it's a list, convert to dict
                logger.debug(f"Products returned as list with {len(products)} items")
                return {product.get('id'): product for product in products}
        else:
            logger.warning("No products found in detailed data")
            return {}

    def get_product_details(self, product_id: int, inventory_id: int) -> Dict:
        """
        Get detailed information for specific product

        Args:
            product_id (int): Product ID
            inventory_id (int): Inventory ID

        Returns:
            Dict: Detailed product data
        """
        detailed_products = self.get_products_detailed([product_id], inventory_id)
        # Convert product_id to string since detailed_products uses string keys
        return detailed_products.get(str(product_id), {})


