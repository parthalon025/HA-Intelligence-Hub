"""Tests for HA discovery module."""

import json
import sys
import os
from unittest.mock import patch, MagicMock, call
from io import BytesIO

# Add bin/ to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin'))

import discover


# =============================================================================
# FIXTURES
# =============================================================================

MOCK_STATES = [
    {
        'entity_id': 'light.living_room',
        'state': 'on',
        'attributes': {
            'friendly_name': 'Living Room Light',
            'brightness': 255
        }
    },
    {
        'entity_id': 'sensor.power_meter',
        'state': '150.5',
        'attributes': {
            'friendly_name': 'Power Meter',
            'device_class': 'power',
            'unit_of_measurement': 'W'
        }
    },
    {
        'entity_id': 'binary_sensor.motion_hallway',
        'state': 'off',
        'attributes': {
            'friendly_name': 'Hallway Motion',
            'device_class': 'motion'
        }
    },
    {
        'entity_id': 'climate.thermostat',
        'state': 'heat',
        'attributes': {
            'friendly_name': 'Thermostat',
            'temperature': 20
        }
    }
]

MOCK_CONFIG = {
    'version': '2026.2.1',
    'location_name': 'Home',
    'time_zone': 'America/New_York'
}

MOCK_SERVICES = [
    {'domain': 'light', 'services': {}},
    {'domain': 'sensor', 'services': {}},
    {'domain': 'climate', 'services': {}}
]

MOCK_ENTITY_REGISTRY = [
    {
        'entity_id': 'light.living_room',
        'platform': 'hue',
        'disabled_by': None,
        'hidden_by': None
    },
    {
        'entity_id': 'sensor.power_meter',
        'platform': 'utility_meter',
        'disabled_by': None,
        'hidden_by': None
    }
]

MOCK_DEVICE_REGISTRY = [
    {
        'id': 'device_1',
        'name': 'Philips Hue Bridge',
        'manufacturer': 'Philips',
        'model': 'BSB002'
    }
]

MOCK_AREA_REGISTRY = [
    {
        'area_id': 'living_room',
        'name': 'Living Room'
    }
]


# =============================================================================
# REST API TESTS
# =============================================================================

def test_fetch_rest_api_success():
    """Test successful REST API fetch."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(MOCK_STATES).encode('utf-8')
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = discover.fetch_rest_api('/api/states')

    assert result == MOCK_STATES
    assert len(result) == 4


def test_fetch_rest_api_retry_on_connection_error():
    """Test retry logic on connection errors."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(MOCK_CONFIG).encode('utf-8')
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    # Fail twice, then succeed
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = [
            Exception('Connection refused'),
            Exception('Timeout'),
            mock_response
        ]

        with patch('time.sleep'):  # Don't actually sleep during tests
            result = discover.fetch_rest_api('/api/config', retries=3)

    assert result == MOCK_CONFIG
    assert mock_urlopen.call_count == 3


def test_fetch_rest_api_auth_error_no_retry():
    """Test that auth errors don't retry."""
    from urllib.error import HTTPError

    error = HTTPError('/api/states', 401, 'Unauthorized', {}, BytesIO(b'Invalid token'))

    with patch('urllib.request.urlopen', side_effect=error):
        try:
            discover.fetch_rest_api('/api/states')
            assert False, "Should have raised exception"
        except Exception as e:
            assert 'Authentication failed' in str(e)


def test_fetch_rest_api_exhausted_retries():
    """Test failure after exhausting all retries."""
    with patch('urllib.request.urlopen', side_effect=Exception('Network error')):
        with patch('time.sleep'):
            try:
                discover.fetch_rest_api('/api/states', retries=2)
                assert False, "Should have raised exception"
            except Exception as e:
                assert 'Failed after 2 attempts' in str(e)


# =============================================================================
# WEBSOCKET TESTS
# =============================================================================

def test_websocket_handshake_creation():
    """Test WebSocket handshake HTTP request creation."""
    handshake = discover._create_websocket_handshake('localhost', 8123, '/api/websocket')

    assert b'GET /api/websocket HTTP/1.1' in handshake
    assert b'Host: localhost:8123' in handshake
    assert b'Upgrade: websocket' in handshake
    assert b'Sec-WebSocket-Key:' in handshake
    assert b'Sec-WebSocket-Version: 13' in handshake


def test_websocket_handshake_response_success():
    """Test parsing successful WebSocket handshake response."""
    response = b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n\r\n'

    result = discover._parse_websocket_handshake_response(response)
    assert result is True


def test_websocket_handshake_response_failure():
    """Test parsing failed WebSocket handshake response."""
    response = b'HTTP/1.1 400 Bad Request\r\n\r\n'

    try:
        discover._parse_websocket_handshake_response(response)
        assert False, "Should have raised exception"
    except Exception as e:
        assert 'handshake failed' in str(e)


def test_websocket_frame_creation():
    """Test WebSocket frame creation with masking."""
    payload = '{"type": "auth", "token": "test"}'
    frame = discover._create_websocket_frame(payload)

    # Check frame structure
    assert frame[0] == 0x81  # FIN + text opcode
    assert frame[1] & 0x80  # Mask bit set
    assert len(frame) > len(payload)  # Frame header + mask + payload


def test_fetch_websocket_data_mocked():
    """Test WebSocket fetch with mocked socket."""
    # Mock socket
    mock_sock = MagicMock()

    # Mock responses
    handshake_response = b'HTTP/1.1 101 Switching Protocols\r\n\r\n'
    auth_required_msg = json.dumps({'type': 'auth_required', 'ha_version': '2026.2.1'})
    auth_ok_msg = json.dumps({'type': 'auth_ok', 'ha_version': '2026.2.1'})
    result_msg = json.dumps({
        'id': 1,
        'type': 'result',
        'success': True,
        'result': MOCK_ENTITY_REGISTRY
    })

    # Mock recv to return frames
    def mock_recv(size):
        if mock_recv.call_count == 0:
            mock_recv.call_count += 1
            return handshake_response
        return b''

    mock_recv.call_count = 0
    mock_sock.recv = mock_recv

    # Mock frame parsing
    def mock_parse_frame(sock):
        if mock_parse_frame.call_count == 0:
            mock_parse_frame.call_count += 1
            return auth_required_msg
        elif mock_parse_frame.call_count == 1:
            mock_parse_frame.call_count += 1
            return auth_ok_msg
        else:
            mock_parse_frame.call_count += 1
            return result_msg

    mock_parse_frame.call_count = 0

    with patch('socket.socket', return_value=mock_sock):
        with patch.object(discover, '_parse_websocket_frame', side_effect=mock_parse_frame):
            result = discover.fetch_websocket_data('config/entity_registry/list')

    assert result == MOCK_ENTITY_REGISTRY


# =============================================================================
# CAPABILITY DETECTION TESTS
# =============================================================================

def test_detect_power_monitoring_capability():
    """Test power monitoring capability detection."""
    entities = {e['entity_id']: e for e in MOCK_STATES}
    capabilities = discover.detect_capabilities(entities, MOCK_ENTITY_REGISTRY)

    assert 'power_monitoring' in capabilities
    power_cap = capabilities['power_monitoring']
    assert power_cap['available'] is True
    assert power_cap['total_count'] == 1
    assert power_cap['entities'][0]['entity_id'] == 'sensor.power_meter'


def test_detect_lighting_capability():
    """Test lighting capability detection."""
    entities = {e['entity_id']: e for e in MOCK_STATES}
    capabilities = discover.detect_capabilities(entities, MOCK_ENTITY_REGISTRY)

    assert 'lighting' in capabilities
    light_cap = capabilities['lighting']
    assert light_cap['available'] is True
    assert light_cap['total_count'] == 1
    assert light_cap['entities'][0]['entity_id'] == 'light.living_room'


def test_detect_motion_capability():
    """Test motion sensor capability detection."""
    entities = {e['entity_id']: e for e in MOCK_STATES}
    capabilities = discover.detect_capabilities(entities, MOCK_ENTITY_REGISTRY)

    assert 'motion' in capabilities
    motion_cap = capabilities['motion']
    assert motion_cap['available'] is True
    assert motion_cap['total_count'] == 1
    assert motion_cap['entities'][0]['entity_id'] == 'binary_sensor.motion_hallway'


def test_detect_climate_capability():
    """Test climate capability detection."""
    entities = {e['entity_id']: e for e in MOCK_STATES}
    capabilities = discover.detect_capabilities(entities, MOCK_ENTITY_REGISTRY)

    assert 'climate' in capabilities
    climate_cap = capabilities['climate']
    assert climate_cap['available'] is True
    assert climate_cap['total_count'] == 1
    assert climate_cap['entities'][0]['entity_id'] == 'climate.thermostat'


def test_capability_not_available_when_no_entities():
    """Test that capability is marked as unavailable when no matching entities."""
    # Only include one entity (no vacuum, no EV charging, etc)
    entities = {
        'light.single': {
            'entity_id': 'light.single',
            'state': 'on',
            'attributes': {'friendly_name': 'Single Light'}
        }
    }

    capabilities = discover.detect_capabilities(entities, [])

    assert capabilities['vacuum']['available'] is False
    assert capabilities['vacuum']['total_count'] == 0
    assert capabilities['ev_charging']['available'] is False


def test_capability_entities_limited_to_10():
    """Test that capability entities list is limited to 10 examples."""
    # Create 20 lights
    entities = {}
    for i in range(20):
        entities[f'light.test_{i}'] = {
            'entity_id': f'light.test_{i}',
            'state': 'on',
            'attributes': {'friendly_name': f'Test Light {i}'}
        }

    capabilities = discover.detect_capabilities(entities, [])

    light_cap = capabilities['lighting']
    assert light_cap['total_count'] == 20
    assert len(light_cap['entities']) == 10  # Limited to 10


# =============================================================================
# INTEGRATION TEST
# =============================================================================

def test_discover_all_integration():
    """Test full discovery flow with all mocked APIs."""
    # Mock all API calls
    with patch.object(discover, 'fetch_rest_api') as mock_rest:
        with patch.object(discover, 'fetch_websocket_data') as mock_ws:
            # Configure mocks
            mock_rest.side_effect = [
                MOCK_STATES,    # /api/states
                MOCK_CONFIG,    # /api/config
                MOCK_SERVICES   # /api/services
            ]

            mock_ws.side_effect = [
                MOCK_ENTITY_REGISTRY,  # entity_registry
                MOCK_DEVICE_REGISTRY,  # device_registry
                MOCK_AREA_REGISTRY,    # area_registry
                Exception("Label registry not available")  # label_registry
            ]

            # Run discovery
            result = discover.discover_all()

            # Verify structure
            assert 'discovery_timestamp' in result
            assert result['ha_version'] == '2026.2.1'
            assert result['entity_count'] == 4
            assert 'capabilities' in result
            assert 'entities' in result
            assert 'devices' in result
            assert 'areas' in result
            assert 'integrations' in result

            # Verify capabilities
            assert result['capabilities']['lighting']['available'] is True
            assert result['capabilities']['power_monitoring']['available'] is True
            assert result['capabilities']['motion']['available'] is True

            # Verify entities dict
            assert 'light.living_room' in result['entities']
            assert 'sensor.power_meter' in result['entities']

            # Verify devices dict
            assert 'device_1' in result['devices']

            # Verify areas dict
            assert 'living_room' in result['areas']

            # Verify integrations list
            assert 'light' in result['integrations']
            assert 'climate' in result['integrations']


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
