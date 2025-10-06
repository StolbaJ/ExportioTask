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
            return result['products']
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
        parameters = {
            'inventory_id': inventory_id,
            'products': [
                {
                    'product_id': product_id,
                    'extra_field_2': new_value
                }
            ]
        }

        try:
            result = self._make_request('updateInventoryProducts', parameters)
            return result.get('status') == 'SUCCESS'
        except Exception as e:
            print(f"Chyba při aktualizaci produktu: {str(e)}")
            return False


def main():
    token = "6006390-6000727-7Y05TI6LMN7VFEYOEWGSVINHOE8ZUPBHV9YA6N6STVVSGM02F248NZX4D1KZXLNR"
    client = BaselinkerClient(token)


    print("Fetching available inventories...")
    inventories = client.get_inventories()
    if not inventories:
        print("No inventories found in your Baselinker account.")
        return
    for n in inventories:
        print(f"Inventory ID: {n['inventory_id']}")
    # Use the first available inventory
    inventory_id = inventories[0]['inventory_id']
    print(f"Using inventory_id: {inventory_id}")

    print("Testing connection to Baselinker API...")
    products = client.get_products(inventory_id)
    print(f"Number of products in inventory {inventory_id}: {len(products)}")

    if products:
        print("First product:")
        #first_product = products[0]
        print(f"ID: {products}")



if __name__ == "__main__":
    main()
