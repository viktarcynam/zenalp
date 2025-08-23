"""
JSON parser module for formatting and validating client requests.
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONRequestParser:
    """Parser for JSON request strings and formatting for server communication."""

    VALID_ACTIONS = {
        'ping',
        'get_positions',
        'get_orders',
        'get_option_chain',
        'get_latest_stock_price',
        'get_option_quote',
        'place_order',
        'cancel_order',
        'replace_order',
    }

    REQUIRED_PARAMS = {
        'get_option_chain': ['symbol'],
        'get_latest_stock_price': ['symbol'],
        'get_option_quote': ['symbol'],
        'place_order': ['symbol', 'qty', 'side', 'limit_price'],
        'cancel_order': ['order_id'],
        'replace_order': ['order_id', 'limit_price'],
        'get_positions': [],
    }

    OPTIONAL_PARAMS = {
        'get_orders': ['status'],
        'get_positions': ['symbol'],
    }

    def parse_json_string(self, json_string: str):
        try:
            if not json_string or not json_string.strip():
                return {'success': False, 'error': 'Empty JSON string'}
            parsed_data = json.loads(json_string.strip())
            if not isinstance(parsed_data, dict):
                return {'success': False, 'error': 'JSON must be an object'}
            return {'success': True, 'data': parsed_data}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {'success': False, 'error': f'Invalid JSON format: {e}'}

    def validate_request(self, request_data: dict):
        if 'action' not in request_data:
            return {'success': False, 'error': 'Missing required field: action'}

        action = request_data['action'].lower()
        if action not in self.VALID_ACTIONS:
            return {'success': False, 'error': f'Invalid action: {action}'}

        if action in self.REQUIRED_PARAMS:
            for param in self.REQUIRED_PARAMS[action]:
                if param not in request_data:
                    return {'success': False, 'error': f'Missing required parameter for {action}: {param}'}
                if not request_data[param] and str(request_data[param]).strip() == '':
                     return {'success': False, 'error': f'Required parameter cannot be empty: {param}'}

        return {'success': True, 'message': 'Request validation successful'}

    def format_request(self, json_string: str):
        parse_result = self.parse_json_string(json_string)
        if not parse_result['success']:
            return parse_result

        request_data = parse_result['data']
        validation_result = self.validate_request(request_data)
        if not validation_result['success']:
            return validation_result

        formatted_request = {'action': request_data['action'].lower()}
        for key, value in request_data.items():
            if key != 'action' and value is not None:
                formatted_request[key] = value

        return {'success': True, 'request': formatted_request}

json_parser = JSONRequestParser()
