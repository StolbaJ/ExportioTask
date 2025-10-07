"""
Integration tests for Baselinker API
These tests can be run against actual API with proper token
"""

import pytest
import os
from baselinker_cli import BaselinkerClient


@pytest.mark.integration
class TestBaselinkerIntegration:
    """Integration tests - require real API token (2 most important)"""

    @pytest.fixture
    def client(self):
        """Create client with real token from environment"""
        token = os.getenv('BASELINKER_API_TOKEN')
        if not token:
            pytest.skip("BASELINKER_API_TOKEN not set - skipping integration tests")
        return BaselinkerClient(token)

    @pytest.mark.skipif(
        not os.getenv('BASELINKER_API_TOKEN'),
        reason="Integration test requires BASELINKER_API_TOKEN"
    )
    def test_get_inventories_and_products_real(self, client):
        """Test getting real inventories and products"""
        inventories = client.get_inventories()
        assert isinstance(inventories, list)
        assert len(inventories) > 0
        assert 'inventory_id' in inventories[0]
        
        # Also test getting products from first inventory
        inventory_id = inventories[0]['inventory_id']
        products = client.get_products(inventory_id)
        assert isinstance(products, list)

    @pytest.mark.skipif(
        not os.getenv('BASELINKER_API_TOKEN'),
        reason="Integration test requires BASELINKER_API_TOKEN"
    )
    def test_get_extra_fields_real(self, client):
        """Test getting real extra fields for inventory"""
        inventories = client.get_inventories()
        if inventories:
            inventory_id = inventories[0]['inventory_id']
            extra_fields = client.get_inventory_extra_fields(inventory_id)
            assert isinstance(extra_fields, list)
            if extra_fields:
                assert 'extra_field_id' in extra_fields[0]
                assert 'name' in extra_fields[0]

