"""
Baselinker API Client
Modul pro komunikaci s Baselinker API pro získání a aktualizaci produktů
"""

import requests
import json
from typing import List, Dict

class BaselinkerClient:
    """Klient pro komunikaci s Baselinker API"""

    def __init__(self, token: str):
        """
        Inicializace klienta s API tokenem

        Args:
            token (str): API token pro Baselinker
        """
        self.token = token
        self.base_url = "https://api.baselinker.com/connector.php"
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-BLToken': token
        }

    def _make_request(self, method: str, parameters: Dict = None) -> Dict:
        """
        Vytvoří HTTP požadavek na Baselinker API

        Args:
            method (str): Název API metody
            parameters (Dict): Parametry pro API volání

        Returns:
            Dict: Odpověď z API

        Raises:
            Exception: Pokud dojde k chybě při komunikaci s API
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
        """Získá list všech inventářů"""
        result = self._make_request('getInventories')
        return result.get('inventories', [])

    def get_products(self, inventory_id: int) -> List[Dict]:
        """
        Získá seznam všech produktů z daného inventáře

        Args:
            inventory_id (int): ID inventáře

        Returns:
            List[Dict]: Seznam produktů s jejich údaji
        """
        parameters = {
            'inventory_id': inventory_id
        }

        result = self._make_request('getInventoryProductsList', parameters)

        if 'products' in result:
            # Baselinker API vrací produkty jako slovník s ID jako klíče
            # Musíme to převést na seznam
            products_dict = result['products']
            if isinstance(products_dict, dict):
                return list(products_dict.values())
            else:
                return products_dict
        else:
            return []

    def update_product_field2(self, product_id: int, inventory_id: int, new_value: str) -> bool:
        """
        Aktualizuje druhé doplňkové pole produktu

        Args:
            product_id (int): ID produktu k aktualizaci
            inventory_id (int): ID inventáře
            new_value (str): Nová hodnota pro druhé doplňkové pole

        Returns:
            bool: True pokud byla aktualizace úspěšná
        """
        # Nejdříve získáme dostupné extra fields
        try:
            extra_fields = self.get_inventory_extra_fields(inventory_id)
            print(f"Available extra fields: {extra_fields}")
            
            # Najdeme druhé extra field (index 1)
            if len(extra_fields) < 2:
                print("Inventář nemá dostatek extra fields (potřebujeme alespoň 2).")
                return False
            
            field_id = extra_fields[1]['extra_field_id']  # Druhé pole (index 1)
            field_name = extra_fields[1]['name']
            print(f"Using extra field: {field_name} (ID: {field_id})")
            
        except Exception as e:
            print(f"Chyba při získávání extra fields: {str(e)}")
            return False

        # Nejdříve získáme aktuální data produktu
        try:
            current_product = self.get_product_details(product_id, inventory_id)
            if not current_product:
                print(f"Produkt s ID {product_id} nebyl nalezen v detailních datech.")
                print("Zkusíme získat základní data produktu...")
                
                # Zkusíme získat základní data z getInventoryProductsList
                all_products = self.get_products(inventory_id)
                current_product = None
                for product in all_products:
                    if product.get('id') == product_id:
                        current_product = product
                        break
                
                if not current_product:
                    print(f"Produkt s ID {product_id} nebyl nalezen ani v základních datech.")
                    return False
                
                print(f"Using basic product data: {current_product}")
            else:
                print(f"Current product data: {current_product}")
        except Exception as e:
            print(f"Chyba při získávání dat produktu: {str(e)}")
            return False

        # Získáme název produktu z text_fields nebo hlavní struktury
        product_name = current_product.get('name', '')
        text_fields = current_product.get('text_fields', {})
        if text_fields and 'name' in text_fields:
            product_name = text_fields['name']
        
        # Připravíme parametry pro aktualizaci
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
        
        print(f"Updating with parameters: {parameters}")

        try:
            result = self._make_request('addInventoryProduct', parameters)
            return result.get('status') == 'SUCCESS'
        except Exception as e:
            print(f"Chyba při aktualizaci produktu: {str(e)}")
            return False

    def get_inventory_extra_fields(self, inventory_id: int) -> List[Dict]:
        """
        Získá seznam dostupných extra fields pro inventář

        Args:
            inventory_id (int): ID inventáře

        Returns:
            List[Dict]: Seznam extra fields
        """
        parameters = {
            'inventory_id': inventory_id
        }

        result = self._make_request('getInventoryExtraFields', parameters)
        return result.get('extra_fields', [])

    def get_products_detailed(self, product_ids: List[int], inventory_id: int) -> Dict:
        """
        Získá detailní informace o více produktech najednou

        Args:
            product_ids (List[int]): Seznam ID produktů
            inventory_id (int): ID inventáře

        Returns:
            Dict: Slovník s ID jako klíče a detailní data jako hodnoty
        """
        parameters = {
            'inventory_id': inventory_id,
            'products': product_ids
        }

        result = self._make_request('getInventoryProductsData', parameters)
        print(f"getInventoryProductsData response: {result}")
        
        if 'products' in result and result['products']:
            products = result['products']
            if isinstance(products, dict):
                print(f"Products returned as dict with {len(products)} items")
                return products
            else:
                # Pokud je to seznam, převedeme na slovník
                print(f"Products returned as list with {len(products)} items")
                return {product.get('id'): product for product in products}
        else:
            print("No products found in detailed data")
            return {}

    def get_product_details(self, product_id: int, inventory_id: int) -> Dict:
        """
        Získá detailní informace o konkrétním produktu

        Args:
            product_id (int): ID produktu
            inventory_id (int): ID inventáře

        Returns:
            Dict: Detailní data produktu
        """
        detailed_products = self.get_products_detailed([product_id], inventory_id)
        # Convert product_id to string since detailed_products uses string keys
        return detailed_products.get(str(product_id), {})


