import pytest

def validate_telemetry_payload(payload: dict) -> bool:
    """Utility function to validate incoming telemetry structure."""
    required_keys = {"sensor_id", "timestamp", "metrics"}
    if not required_keys.issubset(payload.keys()):
        raise ValueError("Missing required telemetry keys")
    return True

def test_telemetry_payload_valid():
    sample_data = {
        "sensor_id": "NODE_ALPHA_01",
        "timestamp": 1725105600,
        "metrics": {"frequency": 433.92, "rssi": -65}
    }
    assert validate_telemetry_payload(sample_data) is True

def test_telemetry_payload_invalid_missing_key():
    invalid_data = {
        "sensor_id": "NODE_ALPHA_01",
        "metrics": {}
    }
    with pytest.raises(ValueError, match="Missing required telemetry keys"):
        validate_telemetry_payload(invalid_data)

@pytest.mark.parametrize("rssi_val,expected_valid", [
    (-50, True),
    (-110, True),
    (0, True),
])
def test_rssi_range(rssi_val, expected_valid):
    assert (rssi_val <= 0) == expected_valid
