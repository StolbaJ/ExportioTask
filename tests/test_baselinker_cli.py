"""
Unit tests for BaselinkerClient
"""

import pytest
from unittest.mock import Mock, patch
from baselinker_cli import BaselinkerClient


class TestBaselinkerClient:
    """Test suite for BaselinkerClient class - 5 most important tests"""

    @pytest.fixture
    def client(self):
        """Create a BaselinkerClient instance for testing"""
        return BaselinkerClient("test_token_123")

    @pytest.fixture
    def mock_response(self):
        """Create a mock response object"""
        mock = Mock()
        mock.status_code = 200
        mock.raise_for_status = Mock()
        return mock

    def test_init(self, client):
        """Test client initialization with token and headers"""
        assert client.token == "test_token_123"
        assert client.base_url == "https://api.baselinker.com/connector.php"
        assert client.headers['X-BLToken'] == "test_token_123"
        assert client.headers['Content-Type'] == 'application/x-www-form-urlencoded'

    @patch('baselinker_cli.requests.post')
    def test_get_products(self, mock_post, client, mock_response):
        """Test get_products returns list from dict response"""
        mock_response.json.return_value = {
            'status': 'SUCCESS',
            'products': {
                '123': {'id': 123, 'name': 'Product 1', 'sku': 'TEST1'},
                '456': {'id': 456, 'name': 'Product 2', 'sku': 'TEST2'}
            }
        }
        mock_post.return_value = mock_response

        result = client.get_products(1)

        assert len(result) == 2
        assert result[0]['id'] == 123
        assert result[1]['sku'] == 'TEST2'

    @patch('baselinker_cli.requests.post')
    def test_get_inventory_extra_fields(self, mock_post, client, mock_response):
        """Test getting extra fields for inventory"""
        mock_response.json.return_value = {
            'status': 'SUCCESS',
            'extra_fields': [
                {'extra_field_id': 467, 'name': 'Field 1'},
                {'extra_field_id': 484, 'name': 'Field 2'}
            ]
        }
        mock_post.return_value = mock_response

        result = client.get_inventory_extra_fields(1)

        assert len(result) == 2
        assert result[0]['extra_field_id'] == 467
        assert result[1]['name'] == 'Field 2'

    @patch.object(BaselinkerClient, 'get_inventory_extra_fields')
    @patch.object(BaselinkerClient, 'get_product_details')
    @patch('baselinker_cli.requests.post')
    def test_update_product_field2_success(self, mock_post, mock_get_details, 
                                          mock_get_fields, client, mock_response):
        """Test successful product field2 update"""
        # Mock extra fields
        mock_get_fields.return_value = [
            {'extra_field_id': 467, 'name': 'Field 1'},
            {'extra_field_id': 484, 'name': 'Field 2'}
        ]
        
        # Mock product details
        mock_get_details.return_value = {
            'id': 123,
            'sku': 'TEST1',
            'ean': '1234567890',
            'text_fields': {'name': 'Test Product'}
        }
        
        # Mock update response
        mock_response.json.return_value = {'status': 'SUCCESS'}
        mock_post.return_value = mock_response

        result = client.update_product_field2(123, 1, 'new_value')

        assert result is True
        mock_get_fields.assert_called_once_with(1)
        mock_get_details.assert_called_once_with(123, 1)

    @patch('baselinker_cli.requests.post')
    def test_make_request_api_error(self, mock_post, client, mock_response):
        """Test API error handling"""
        mock_response.json.return_value = {
            'status': 'ERROR',
            'error_message': 'Invalid API key'
        }
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            client._make_request('testMethod')

        assert 'API Error' in str(exc_info.value)
        assert 'Invalid API key' in str(exc_info.value)

